# planner/models.py
from django.db import models

class UserProfile(models.Model):
    
    FREQUENCY = [
        ( 'INICIANTE', 'Iniciante 1 - 2 vezes'),
        ('INTERMEDIARIO', 'Mediano 2 - 4 Vezes'),
        ('FREQUENTE', 'Alta 4 - 5 Vezes'),
        ('MAXIMO', 'Insano 5 - 7 Vezes')
    ]
    
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    weight = models.FloatField()
    height = models.FloatField()
    workout_frequency = models.CharField(max_length=50, choices = FREQUENCY, default= 'INICIANTE')
    goals = models.TextField()
    dietary_restrictions = models.TextField()
    extra_notes = models.TextField()
    

    def __str__(self):
        return self.name

class WorkoutPlan(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Workout Plan for {self.user.name}"

class DietPlan(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diet Plan for {self.user.name}"