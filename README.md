# Telegram Gemini Bot 🤖

Bot de Telegram inteligente que utiliza la API de Google Gemini para generar respuestas conversacionales.

## 🌟 Características

- Conversación general con IA
- Traducción de idiomas
- Generación de código
- Soporte para chats privados y grupos

## 🛠 Requisitos

- Python 3.8+
- Telegram Bot Token
- Google Gemini API Key

## 📦 Instalación

1. Clonar el repositorio
```bash
git clone https://github.com/franklinsantaella/telegram-gemini-bot.git
cd telegram-gemini-bot
```

2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno
- Copiar .env.example a .env
- Añadir tus tokens de Telegram y Gemini

## 🚀 Uso

Comandos disponibles:
- `/start`: Iniciar el bot
- `/help`: Mostrar ayuda
- `/translate`: Traducir texto
- `/code`: Generar código

## 🔐 Configuración

Crear un archivo .env con:
```
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
```

## 📄 Licencia

MIT License
