# planner/urls.py
from django.urls import path
from .views import InputFormView, GeneratePlanView, WorkoutPlanDetailView, DietPlanDetailView, RegisterView, LoginView, LogoutView, MyWorkoutView, toggle_exercise_progress

urlpatterns = [
    path('', InputFormView.as_view(), name='input-form'),
    path('generate-plan/', GeneratePlanView.as_view(), name='generate-plan'),
    path('workout-plan/<int:user_id>/', WorkoutPlanDetailView.as_view(), name='workout-plan-detail'),
    path('diet-plan/<int:user_id>/', DietPlanDetailView.as_view(), name='diet-plan-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('meu-treino/', MyWorkoutView.as_view(), name='my-workout'),
    path('toggle-exercise-progress/', toggle_exercise_progress, name='toggle-exercise-progress'),
]