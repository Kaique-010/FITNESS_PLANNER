
from xml.dom.minidom import Attr
from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'name', 'age', 'weight', 'height', 'workout_frequency',
            'goals', 'dietary_restrictions', 'extra_notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Idade'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Altura'}),
            'workout_frequency': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Frequencia de Treinos'}),
            'goals': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Objetivos'}),
            'dietary_restrictions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Restrições?'}),
            'extra_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Extra'})
        }