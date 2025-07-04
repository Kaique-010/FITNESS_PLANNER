from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import UserProfile, WorkoutPlan, DietPlan
from .forms import UserProfileForm, CustomUserCreationForm, CustomAuthenticationForm
from .deepseek_api import DeepSeekAPI
import google.generativeai as genai
import os
from django.http import JsonResponse
from .models import WorkoutDay, Exercise, WorkoutProgress
from django.views.decorators.csrf import csrf_exempt
import re
import json


@method_decorator(login_required, name='dispatch')
class InputFormView(TemplateView):
    """Renderiza o formulário de entrada de dados."""
    template_name = 'planner/input_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preenche o formulário com dados do perfil do usuário logado
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={
            'name': self.request.user.username,
            'age': 0, 'weight': 0, 'height': 0, 'workout_frequency': 'INICIANTE',
            'goals': '', 'dietary_restrictions': '', 'extra_notes': ''
        })
        context['form'] = UserProfileForm(instance=profile)
        return context



genai.configure(api_key=os.getenv('GOOGLE_API_KEY')) 

def parse_and_create_days_exercises_json(plan_obj):
    WorkoutDay.objects.filter(plan=plan_obj).delete()
    try:
        import json
        import re
        # Remove blocos de markdown ```json ... ```
        plan_text = plan_obj.plan.strip()
        plan_text = re.sub(r"^```json|^```|```$", "", plan_text, flags=re.MULTILINE).strip()
        # Corrige valores de repeticoes: Máximo sem aspas para "Máximo"
        plan_text = re.sub(r'(\"repeticoes\": )Máximo', r'\1"Máximo"', plan_text)
        data = json.loads(plan_text)
        for dia in data.get('dias', []):
            day_name = dia.get('dia', '').capitalize()
            if not day_name:
                continue
            day_obj = WorkoutDay.objects.create(plan=plan_obj, day_of_week=day_name)
            for ex in dia.get('exercicios', []):
                if isinstance(ex, dict):
                    nome = ex.get('nome', '').strip()
                    series = ex.get('series')
                    repeticoes = ex.get('repeticoes')
                    descanso = ex.get('descanso')
                    if nome:
                        Exercise.objects.create(day=day_obj, name=nome, series=series, repeticoes=repeticoes, descanso=descanso)
                elif isinstance(ex, str):
                    nome = ex.strip()
                    if nome:
                        Exercise.objects.create(day=day_obj, name=nome)
    except Exception as e:
        print(f'Erro ao parsear JSON do plano: {e}')

@method_decorator(login_required, name='dispatch')
class GeneratePlanView(View):
    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            user = profile
            prompt = (
                f"Crie um plano de treino SEMANAL personalizado para {user.name}, {user.age} anos, "
                f"pesando {user.weight} kg e com {user.height} cm de altura. "
                f"O usuário treina {user.workout_frequency} e tem como meta {user.goals}. "
                f"Restrições alimentares: {user.dietary_restrictions}. "
                f"Observações extras: {user.extra_notes}. "
                f"\n\nResponda SOMENTE com dois JSONs, um para treino e um para dieta, exatamente assim:\n"
                f"TREINO:\n{{'dias': [{{'dia': 'Segunda', 'exercicios': ['Agachamento', 'Flexão']}}, ...]}}\n"
                f"DIETA:\n{{'dias': [{{'dia': 'Segunda', 'refeicoes': [{{'nome': 'Café da manhã', 'itens': ['Ovos', 'Aveia']}}, ...]}}, ...]}}\n"
                f"Sem explicações, sem comentários, apenas os dois JSONs puros, começando cada um na linha seguinte ao título."
            )
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                resposta = response.text.strip()
                print("RESPOSTA DO MODELO:", resposta)
                # Extrai os dois JSONs do texto
                treino_json = ''
                dieta_json = ''
                for bloco in resposta.split('DIETA:'):
                    if 'TREINO:' in bloco:
                        treino_json = bloco.split('TREINO:')[1].strip()
                    else:
                        dieta_json = bloco.strip()
                # Apaga planos antigos do usuário
                WorkoutPlan.objects.filter(user=request.user).delete()
                DietPlan.objects.filter(user=request.user).delete()
                # Cria novo plano de treino
                workout_plan = WorkoutPlan.objects.create(user=request.user, plan=treino_json)
                # Cria novo plano de dieta
                diet_plan = DietPlan.objects.create(user=request.user, plan=dieta_json)
                # Só parseia se treino_json não estiver vazio
                if not treino_json:
                    print("ERRO: treino_json vazio! Não foi possível criar os dias/exercícios.")
                    return render(request, 'planner/input_form.html', {'form': form, 'error': 'O modelo de IA não retornou o plano de treino corretamente. Tente novamente ou ajuste o prompt.'})
                parse_and_create_days_exercises_json(workout_plan)
                return redirect('workout-plan-detail', user_id=profile.id)
            except Exception as e:
                return render(request, 'planner/input_form.html', {'form': form, 'error': f'Erro ao gerar plano: {str(e)}'})
        return render(request, 'planner/input_form.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class WorkoutPlanDetailView(DetailView):
    """Exibe o plano de treino gerado."""
    model = WorkoutPlan
    template_name = 'planner/workout_plan.html'
    context_object_name = 'workout_plan'

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(UserProfile, id=user_id)
        return WorkoutPlan.objects.filter(user=profile.user).order_by('-created_at').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.object.user.profile
        import json, re
        plan_text = self.object.plan.strip() if self.object.plan else ''
        plan_text = re.sub(r"^```json|^```|```$", "", plan_text, flags=re.MULTILINE).strip()
        plan_text = re.sub(r'("repeticoes": )Máximo', r'\1"Máximo"', plan_text)
        try:
            plan_data = json.loads(plan_text)
            context['plan_data'] = plan_data
            context['plan_error'] = None
        except Exception as e:
            context['plan_data'] = None
            context['plan_error'] = f'Erro ao processar plano de treino: {e}'
        return context

@method_decorator(login_required, name='dispatch')
class DietPlanDetailView(DetailView):
    """Exibe o plano de dieta gerado."""
    model = DietPlan
    template_name = 'planner/diet_plan.html'
    context_object_name = 'diet_plan'

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(UserProfile, id=user_id)
        return get_object_or_404(DietPlan, user=profile.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.object.user.profile
        import json, re
        plan_text = self.object.plan.strip() if self.object.plan else ''
        plan_text = re.sub(r"^```json|^```|```$", "", plan_text, flags=re.MULTILINE).strip()
        try:
            plan_data = json.loads(plan_text)
            context['plan_data'] = plan_data
            context['plan_error'] = None
        except Exception as e:
            context['plan_data'] = None
            context['plan_error'] = f'Erro ao processar plano de dieta: {e}'
        return context

class RegisterView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'planner/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Cria perfil fitness vazio
            UserProfile.objects.create(user=user, name=user.username, age=0, weight=0, height=0, workout_frequency='INICIANTE', goals='', dietary_restrictions='', extra_notes='')
            return redirect('input-form')
        return render(request, 'planner/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, 'planner/login.html', {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('my-workout')
        return render(request, 'planner/login.html', {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

@method_decorator(login_required, name='dispatch')
class MyWorkoutView(View):
    def get(self, request):
        plan = WorkoutPlan.objects.filter(user=request.user).order_by('-created_at').first()
        if not plan:
            return render(request, 'planner/my_workout.html', {'plan': None, 'days': [], 'selected_day': None, 'exercises': [], 'done': 0, 'total': 0})
        days = WorkoutDay.objects.filter(plan=plan).order_by('id')
        return render(request, 'planner/my_workout.html', {'plan': plan, 'days': days, 'selected_day': None, 'exercises': [], 'done': 0, 'total': 0})

@method_decorator(login_required, name='dispatch')
class DiaTreinoView(View):
    def get(self, request, day_id):
        plan = WorkoutPlan.objects.filter(user=request.user).order_by('-created_at').first()
        days = WorkoutDay.objects.filter(plan=plan).order_by('id')
        selected_day = get_object_or_404(WorkoutDay, id=day_id, plan=plan)
        exercises = Exercise.objects.filter(day=selected_day)
        ex_data = []
        done_count = 0
        for ex in exercises:
            progress = WorkoutProgress.objects.filter(user=request.user, exercise=ex, date__isnull=False, completed=True).exists()
            if progress:
                done_count += 1
            ex_data.append({'obj': ex, 'done': progress})
        all_done = done_count == len(ex_data) and len(ex_data) > 0
        return render(request, 'planner/my_workout.html', {
            'plan': plan,
            'days': days,
            'selected_day': selected_day,
            'exercises': ex_data,
            'done': done_count,
            'total': len(ex_data),
            'all_done': all_done
        })

@csrf_exempt
@login_required
def toggle_exercise_progress(request):
    if request.method == 'POST':
        ex_id = request.POST.get('exercise_id')
        exercise = get_object_or_404(Exercise, id=ex_id)
        progress, created = WorkoutProgress.objects.get_or_create(user=request.user, exercise=exercise)
        progress.completed = not progress.completed
        progress.save()
        return JsonResponse({'success': True, 'completed': progress.completed})
    return JsonResponse({'success': False}, status=400)
