from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, DetailView
from .models import UserProfile, WorkoutPlan, DietPlan
from .forms import UserProfileForm
from .deepseek_api import DeepSeekAPI
import google.generativeai as genai
import os


class InputFormView(TemplateView):
    """Renderiza o formulário de entrada de dados."""
    template_name = 'planner/input_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserProfileForm()  # Adiciona o formulário ao contexto
        return context



genai.configure(api_key=os.getenv('GOOGLE_API_KEY')) 

class GeneratePlanView(View):
    """Processa o formulário e gera os planos de dieta e treino."""
    def post(self, request):
        print("🔹 Requisição recebida na GeneratePlanView")
        form = UserProfileForm(request.POST)
        if form.is_valid():
            print("✅ Formulário válido!")
            user = form.save(commit=False)  # Salvar sem confirmar para inspecionar
            user.save()
            print(f"🆕 Usuário salvo: {user.name}")

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
                workout_plan = WorkoutPlan.objects.create(user=user, plan=workout_plan_text)
                diet_plan = DietPlan.objects.create(user=user, plan=diet_plan_text)

                print("✅ Planos gerados com sucesso!")
                print(f"🏋️ Plano de treino: {workout_plan_text}")
                print(f"🍽️ Plano de dieta: {diet_plan_text}")

                # Redireciona para a página de exibição do plano de treino
                return redirect('workout-plan-detail', user_id=user.id)

            except Exception as e:
                print(f"❌ Erro ao gerar plano: {e}")
                return render(request, 'planner/input_form.html', {'form': form, 'error': f'Erro ao gerar plano: {str(e)}'})

        print("❌ Formulário inválido!")
        return render(request, 'planner/input_form.html', {'form': form})


class WorkoutPlanDetailView(DetailView):
    """Exibe o plano de treino gerado."""
    model = WorkoutPlan
    template_name = 'planner/workout_plan.html'
    context_object_name = 'workout_plan'

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(UserProfile, id=user_id)
        return get_object_or_404(WorkoutPlan, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.object.user  # Adiciona o usuário ao contexto
        return context

class DietPlanDetailView(DetailView):
    """Exibe o plano de dieta gerado."""
    model = DietPlan
    template_name = 'planner/diet_plan.html'
    context_object_name = 'diet_plan'

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(UserProfile, id=user_id)
        return get_object_or_404(DietPlan, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.object.user  # Adiciona o usuário ao contexto
        return context
