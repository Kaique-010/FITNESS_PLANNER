# planner/urls.py
from django.urls import path
from .views import InputFormView, GeneratePlanView, WorkoutPlanDetailView, DietPlanDetailView

urlpatterns = [
    path('', InputFormView.as_view(), name='input-form'),  # Página inicial com o formulário
    path('generate-plan/', GeneratePlanView.as_view(), name='generate-plan'),  # Processa o formulário
    path('workout-plan/<int:user_id>/', WorkoutPlanDetailView.as_view(), name='workout-plan-detail'),  # Plano de treino
    path('diet-plan/<int:user_id>/', DietPlanDetailView.as_view(), name='diet-plan-detail'),  # Plano de dieta
]