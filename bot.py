import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Cargar variables de entorno ANTES de usarlas
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Verificar que el token esté presente
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No se encontró el token de Telegram. Verifica tu archivo .env")

if not GEMINI_API_KEY:
    raise ValueError("No se encontró la API key de Gemini. Verifica tu archivo .env")

# Configurar API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /start"""
    await update.message.reply_text('¡Hola! Soy un bot de Telegram que usa Gemini. Envíame un mensaje y te responderé.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar mensajes de texto"""
    user_message = update.message.text
    
    try:
        # Generar respuesta con Gemini
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error al procesar mensaje: {e}")
        await update.message.reply_text("Lo siento, hubo un error procesando tu mensaje.")

def main() -> None:
    """Función principal para iniciar el bot"""
    # Crear la aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registrar manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Iniciar el bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()