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

@method_decorator(login_required, name='dispatch')
class GeneratePlanView(View):
    """Processa o formulário e gera os planos de dieta e treino."""
    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Geração do plano segue igual, mas usando o perfil do usuário logado
            user = profile
            prompt = (
                f"Crie um plano personalizado para {user.name}, {user.age} anos, "
                f"pesando {user.weight} kg e com {user.height} cm de altura. "
                f"O usuário treina {user.workout_frequency} e tem como meta {user.goals}. "
                f"Restrições alimentares: {user.dietary_restrictions}. "
                f"Observações extras: {user.extra_notes}. "
                f"Por favor, sendo um especilista em treinos e dietas forneça um plano de treino e uma dieta semanal detalhados."
                f"Sem Informações irrelevantes apenas as informações solicitadas"
            )

            try:
                # Gera o plano com a API Gemini
                model = genai.GenerativeModel("gemini-1.5-flash")

                treino_response = model.generate_content(f"Plano de treino: {prompt}")
                dieta_response = model.generate_content(f"Plano de dieta: {prompt}")

                workout_plan_text = treino_response.text.strip()
                diet_plan_text = dieta_response.text.strip()

                # Salva os planos no banco de dados
                workout_plan = WorkoutPlan.objects.create(user=request.user, plan=workout_plan_text)
                diet_plan = DietPlan.objects.create(user=request.user, plan=diet_plan_text)

                print("✅ Planos gerados com sucesso!")
                print(f"🏋️ Plano de treino: {workout_plan_text}")
                print(f"🍽️ Plano de dieta: {diet_plan_text}")

                # Redireciona para a página de exibição do plano de treino
                return redirect('workout-plan-detail', user_id=profile.id)

            except Exception as e:
                print(f"❌ Erro ao gerar plano: {e}")
                return render(request, 'planner/input_form.html', {'form': form, 'error': f'Erro ao gerar plano: {str(e)}'})

        print("❌ Formulário inválido!")
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
        context['user'] = self.object.user.profile  # Passa o perfil para o template
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
        context['user'] = self.object.user.profile  # Passa o perfil para o template
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
            return render(request, 'planner/my_workout.html', {'plan': None})
        days = WorkoutDay.objects.filter(plan=plan).order_by('id')
        days_data = []
        for day in days:
            exercises = Exercise.objects.filter(day=day)
            ex_data = []
            done_count = 0
            for ex in exercises:
                progress = WorkoutProgress.objects.filter(user=request.user, exercise=ex, date__isnull=False, completed=True).exists()
                if progress:
                    done_count += 1
                ex_data.append({'obj': ex, 'done': progress})
            days_data.append({'day': day, 'exercises': ex_data, 'total': len(ex_data), 'done': done_count})
        return render(request, 'planner/my_workout.html', {'plan': plan, 'days_data': days_data})

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
