# planner/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, DetailView
from .models import UserProfile, WorkoutPlan, DietPlan
from .forms import UserProfileForm
from .deepseek_api import DeepSeekAPI

class InputFormView(TemplateView):
    """Renderiza o formulário de entrada de dados."""
    template_name = 'planner/input_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserProfileForm()  # Adiciona o formulário ao contexto
        return context

class GeneratePlanView(View):
    """Processa o formulário e gera os planos de dieta e treino."""
    def post(self, request):
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Salva os dados do usuário no banco de dados
            user = form.save()

            # Formata o prompt com os dados do usuário
            prompt = (
                f"Crie um plano personalizado para {user.name}, {user.age} anos, "
                f"pesando {user.weight} kg e com {user.height} cm de altura. "
                f"O usuário treina {user.workout_frequency} e tem como meta {user.goals}. "
                f"Restrições alimentares: {user.dietary_restrictions}. "
                f"Observações extras: {user.extra_notes}. "
                f"Por favor, forneça um plano de treino e uma dieta semanal detalhados."
            )

            # Gera os planos usando a API do DeepSeek
            deepseek_api = DeepSeekAPI()
            workout_plan = deepseek_api.generate_workout_plan(prompt)
            diet_plan = deepseek_api.generate_diet_plan(prompt)

            # Salva os planos gerados no banco de dados
            WorkoutPlan.objects.create(user=user, plan=workout_plan)
            DietPlan.objects.create(user=user, plan=diet_plan)

            # Redireciona para a página de resultados
            return redirect('workout-plan-detail', user_id=user.id)
        
        # Se o formulário não for válido, renderiza o formulário novamente com erros
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