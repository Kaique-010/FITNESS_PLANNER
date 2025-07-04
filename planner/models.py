# planner/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    FREQUENCY = [
        ('INICIANTE', 'Iniciante 1 - 2 vezes'),
        ('INTERMEDIARIO', 'Mediano 2 - 4 Vezes'),
        ('FREQUENTE', 'Alta 4 - 5 Vezes'),
        ('MAXIMO', 'Insano 5 - 7 Vezes')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    weight = models.FloatField()
    height = models.FloatField()
    workout_frequency = models.CharField(max_length=50, choices=FREQUENCY, default='INICIANTE')
    goals = models.TextField()
    dietary_restrictions = models.TextField()
    extra_notes = models.TextField()
    def __str__(self):
        return self.user.username

class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Plano de treino de {self.user.username} em {self.created_at.date()}"

class WorkoutDay(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='days')
    day_of_week = models.CharField(max_length=10)  # Ex: 'Segunda'
    def __str__(self):
        return f"{self.day_of_week} - {self.plan}"

class Exercise(models.Model):
    day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    series = models.IntegerField(null=True, blank=True)
    repeticoes = models.CharField(max_length=20, null=True, blank=True)
    descanso = models.IntegerField(null=True, blank=True)  # segundos
    def __str__(self):
        return f"{self.name} ({self.day.day_of_week})"

class WorkoutProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progress')
    date = models.DateField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} - {self.date} - {'Feito' if self.completed else 'Pendente'}"

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans')
    plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Plano de dieta de {self.user.username} em {self.created_at.date()}"