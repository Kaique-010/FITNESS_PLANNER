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
        print("🔹 Requisição recebida na GeneratePlanView")
        form = UserProfileForm(request.POST)
        if form.is_valid():
            print("✅ Formulário válido!")
            user = form.save(commit=False)  # Salvar sem confirmar para inspecionar
            user.save()
            print(f"🆕 Usuário salvo: {user.name}")

            model_name = request.POST.get('model', 'gemini-1.5-flash')  # Correção do request.data
            prompt = (
                f"Crie um plano personalizado para {user.name}, {user.age} anos, "
                f"pesando {user.weight} kg e com {user.height} cm de altura. "
                f"O usuário treina {user.workout_frequency} e tem como meta {user.goals}. "
                f"Restrições alimentares: {user.dietary_restrictions}. "
                f"Observações extras: {user.extra_notes}. "
                f"Por favor, forneça um plano de treino e uma dieta semanal detalhados."
            )

            # Verifica se a API está configurada corretamente
            deepseek_api = DeepSeekAPI()
            print(f"🔑 Usando chave da API: {deepseek_api.api_key}")
            if not deepseek_api.api_key:
                return render(request, 'planner/input_form.html', {'form': form, 'error': 'Erro: Chave da API não configurada.'})

            # Gera os planos usando a API do DeepSeek
            try:
                workout_plan = deepseek_api.generate_workout_plan(prompt)
                diet_plan = deepseek_api.generate_diet_plan(prompt)
                print("✅ Planos gerados com sucesso!")

                # Salva os planos no banco de dados
                WorkoutPlan.objects.create(user=user, plan=workout_plan)
                DietPlan.objects.create(user=user, plan=diet_plan)
                
                print(f"💾 Planos salvos para {user.name}")

                # Redireciona para a página de resultados
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