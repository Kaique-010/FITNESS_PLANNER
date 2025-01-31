# deepseek_api.py
from django.conf import settings

class DeepSeekAPI:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY

    def generate_workout_plan(self, prompt):
        # Exemplo de uso da chave da API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Aqui você faria a requisição à API do DeepSeek
        # Exemplo fictício:
        workout_plan = f"Plano de Treino gerado com a chave {self.api_key}"
        return workout_plan

    def generate_diet_plan(self, prompt):
        # Similar ao método acima
        diet_plan = f"Plano de Dieta gerado com a chave {self.api_key}"
        return diet_plan