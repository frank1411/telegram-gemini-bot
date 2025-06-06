import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar la API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Listar modelos disponibles
print("Modelos disponibles en tu plan gratuito:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} (tokens: {m.input_token_limit})")
except Exception as e:
    print(f"Error al listar modelos: {e}")