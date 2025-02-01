import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Cargar variables de entorno ANTES de usarlas
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Obtener credenciales
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
# Convertir la cadena de IDs en una lista
TELEGRAM_DESTINATIONS = os.getenv('TELEGRAM_GROUPS_AND_CHANNELS', '').split(',')

# Verificar que el token esté presente
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No se encontró el token de Telegram. Verifica tu archivo .env")

if not GEMINI_API_KEY:
    raise ValueError("No se encontró la API key de Gemini. Verifica tu archivo .env")

# Configurar API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini
model = genai.GenerativeModel('gemini-pro')

# Función para generar un artículo con Gemini
def generar_articulo():
    try:
        prompt = "Genera un artículo corto y original sobre un tema actual relevante para un público general. Debe tener una introducción, un desarrollo y una conclusión. El tono debe ser neutral y objetivo. Extensión aproximada de 200-300 palabras."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error al generar el artículo: {e}")
        return None

# Función para publicar artículo en múltiples destinos
async def publicar_articulo(context: ContextTypes.DEFAULT_TYPE, articulo: str) -> None:
    """Publicar artículo en múltiples destinos"""
    if not TELEGRAM_DESTINATIONS:
        logging.warning("No se han configurado destinos para publicar.")
        return
    
    for destination in TELEGRAM_DESTINATIONS:
        try:
            await context.bot.send_message(
                chat_id=destination.strip(), 
                text=articulo
            )
            logging.info(f"Artículo publicado en {destination}")
        except Exception as e:
            logging.error(f"Error publicando en {destination}: {e}")

# Comandos de inicio y ayuda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de inicio del bot"""
    welcome_message = (
        "¡Hola! Soy un bot de Telegram impulsado por Gemini AI 🤖\n\n"
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar ayuda\n"
        "/translate - Traducir texto\n"
        "/code - Generar código\n"
        "/generar - Generar y enviar un artículo\n"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostrar ayuda detallada"""
    help_text = (
        "🤖 Ayuda del Bot de Gemini AI 🤖\n\n"
        "Puedes interactuar conmigo de varias formas:\n"
        "1. Envía un mensaje de texto y conversaré contigo\n"
        "2. Usa los siguientes comandos especiales:\n"
        "   /start - Iniciar el bot\n"
        "   /help - Mostrar esta ayuda\n"
        "   /translate [idioma_origen] [idioma_destino] [texto] - Traducir texto\n"
        "   /code [lenguaje] [descripción] - Generar código\n"
        "   /generar - Generar un artículo para aprobar\n"
    )
    await update.message.reply_text(help_text)

# Comando para generar artículo
async def generar_y_enviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generar y enviar artículo para aprobación"""
    articulo = generar_articulo()
    if articulo:
        # Crear botones de aprobación
        keyboard = [
            [
                InlineKeyboardButton("Aprobar", callback_data='approve'),
                InlineKeyboardButton("Rechazar", callback_data='reject')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar para aprobación
        await context.bot.send_message(
            chat_id=TELEGRAM_USER_ID, 
            text=f"¿Aprobar este artículo?\n\n{articulo}", 
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Error al generar el artículo.")

# Manejar botones de aprobación
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar interacción con botones de aprobación"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'approve':
        # Extraer artículo del mensaje original
        articulo = query.message.text.replace("¿Aprobar este artículo?\n\n", "")
        
        # Publicar en todos los destinos configurados
        await publicar_articulo(context, articulo)
        
        await query.edit_message_text(text="Artículo aprobado y publicado.")
    
    elif query.data == 'reject':
        await query.edit_message_text(text="Artículo rechazado.")

# Comando de traducción
async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traducir texto entre idiomas"""
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /translate [idioma_origen] [idioma_destino] [texto]")
        return
    
    src_lang, dest_lang = context.args[0], context.args[1]
    text = " ".join(context.args[2:])
    
    try:
        prompt = f"Traduce el siguiente texto del {src_lang} al {dest_lang}: {text}"
        response = model.generate_content(prompt)
        await update.message.reply_text(f"Traducción: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"Error en la traducción: {str(e)}")

# Comando para generar código
async def code_generator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generar código basado en descripción"""
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /code [lenguaje] [descripción]")
        return
    
    language = context.args[0]
    description = " ".join(context.args[1:])
    
    try:
        prompt = f"Genera código en {language} para: {description}"
        response = model.generate_content(prompt)
        await update.message.reply_text(f"Código generado:\n```{language}\n{response.text}\n```")
    except Exception as e:
        await update.message.reply_text(f"Error generando código: {str(e)}")

# Manejar mensajes de texto generales
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

# Función principal para iniciar el bot
def main() -> None:
    """Función principal para iniciar el bot"""
    # Crear la aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registrar manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("code", code_generator))
    application.add_handler(CommandHandler("generar", generar_y_enviar))
    
    # Registrar manejador de botones
    application.add_handler(CallbackQueryHandler(button))
    
    # Registrar manejador de mensajes generales
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Iniciar el bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()