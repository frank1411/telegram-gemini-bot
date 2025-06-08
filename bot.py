import os
import logging
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
import uvicorn

# Cargar variables de entorno ANTES de usarlas
load_dotenv(override=True)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Obtener credenciales
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
# Convertir la cadena de IDs en una lista, eliminando elementos vacíos
TELEGRAM_DESTINATIONS = [dest.strip() for dest in os.getenv('TELEGRAM_GROUPS_AND_CHANNELS', '').split(',') if dest.strip()]

# Verificar que el token esté presente
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No se encontró el token de Telegram. Verifica tu archivo .env")

if not GEMINI_API_KEY:
    raise ValueError("No se encontró la API key de Gemini. Verifica tu archivo .env")

# Configurar API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini
#model = genai.GenerativeModel('gemini-pro')
#model = genai.GenerativeModel('gemini-1.0-pro')
#model = genai.GenerativeModel('gemini-1.5-pro-latest')
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Estados para la conversación de generación de artículos
GENERATE, APPROVE, EDIT = range(3)

# Función para generar un artículo con Gemini
def generar_articulo(tema_especifico=None):
    try:
        # Si no se proporciona un tema específico, usar el prompt original
        if not tema_especifico:
            prompt = """Eres un analista experto en apuestas deportivas, especializado en baloncesto de la NBA. 
            Dominas conceptos avanzados como bankroll, stake, ROI, handicap, over/under, gestión de riesgo, yield y rollover.

            Instrucciones del artículo:
            Extensión: 250-300 palabras.
            Tema: Estrategias avanzadas de apuestas en la NBA.
            Nivel: Profesional y técnico.
            Tono: Objetivo, basado en datos y análisis riguroso.
            Audiencia: Apostadores avanzados y analistas deportivos.
            Posibles enfoques:
            1. Gestión avanzada del bankroll en apuestas NBA.
            2. Estrategias de stake y ROI en baloncesto.
            3. Análisis de handicaps y over/under en la NBA.
            4. Técnicas de mitigación de riesgo en apuestas deportivas.
            5. Optimización del yield mediante modelos estadísticos.

            Requisitos del contenido:
            ✅ Uso de terminología técnica precisa.
            ✅ Incluir ejemplos prácticos y casos reales.
            ✅ Explicaciones claras y estructuradas de conceptos complejos.
            ✅ Insights basados en datos recientes y análisis estadístico.

            El artículo debe reflejar un conocimiento profundo del mercado de apuestas en la NBA, 
            proporcionando estrategias accionables respaldadas por evidencia."""
        else:
            # Si se proporciona un tema específico, usarlo en el prompt
            prompt = f"""Eres un analista experto en apuestas deportivas, especializado en baloncesto de la NBA. 
            Dominas conceptos avanzados como bankroll, stake, ROI, handicap, over/under, gestión de riesgo, yield y rollover.

            Instrucciones del artículo:
            Extensión: 250-300 palabras.
            Tema específico: {tema_especifico}
            Nivel: Profesional y técnico.
            Tono: Objetivo, basado en datos y análisis riguroso.
            Audiencia: Apostadores avanzados y analistas deportivos.

            Requisitos del contenido:
            ✅ Uso de terminología técnica precisa.
            ✅ Incluir ejemplos prácticos y casos reales relacionados con {tema_especifico}.
            ✅ Explicaciones claras y estructuradas de conceptos complejos.
            ✅ Insights basados en datos recientes y análisis estadístico.

            El artículo debe reflejar un conocimiento profundo del mercado de apuestas en la NBA, 
            proporcionando estrategias accionables respaldadas por evidencia."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error al generar el artículo: {e}")
        return None

# Función para publicar artículo en múltiples destinos
async def publicar_articulo(context: ContextTypes.DEFAULT_TYPE, articulo: str) -> None:
    """Publicar artículo en múltiples destinos"""
    # Imprimir los destinos para depuración
    logging.info(f"Destinos configurados: {TELEGRAM_DESTINATIONS}")
    
    if not TELEGRAM_DESTINATIONS:
        logging.warning("No se han configurado destinos para publicar.")
        return
    
    for destination in TELEGRAM_DESTINATIONS:
        try:
            # Usar el ID tal como está, sin modificaciones
            logging.info(f"Intentando enviar a chat_id: {destination}")
            logging.info(f"Longitud del artículo: {len(articulo)} caracteres")
            
            # Intentar enviar el mensaje
            await context.bot.send_message(
                chat_id=destination, 
                text=articulo
            )
            logging.info(f"✅ Artículo publicado exitosamente en {destination}")
        
        except Exception as e:
            # Logging detallado del error
            logging.error(f"❌ Error publicando en {destination}: {str(e)}")
            logging.error(f"Detalles del error: {type(e).__name__}")
            
            # Información adicional de depuración
            if hasattr(e, 'response'):
                logging.error(f"Respuesta del bot: {e.response}")

# Comando de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de inicio del bot"""
    welcome_message = (
        "¡Hola! Soy un bot de Telegram impulsado por Gemini AI 🤖\n\n"
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar ayuda\n"
        "/generar - Generar y enviar un artículo\n"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostrar ayuda detallada"""
    help_text = (
        "🤖 Ayuda del Bot de Gemini AI 🤖\n\n"
        "Puedes interactuar conmigo de varias formas:\n"
        "1. Usa el comando /generar para crear un artículo\n"
        "2. Podrás aprobar, editar o rechazar el artículo generado\n"
    )
    await update.message.reply_text(help_text)

# Función para iniciar la generación de artículos
async def generar_y_enviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Iniciar el proceso de generación de artículos"""
    try:
        # Mensaje inicial
        await update.message.reply_text(
            "🤖 Generador de Artículos de Apuestas NBA 🏀\n\n"
            "Puedes proporcionarme un tema específico o dejar que genere un artículo aleatorio.\n"
            "Escribe un tema o envía /cancelar para salir."
        )
        return GENERATE
    except Exception as e:
        logging.error(f"Error al iniciar generación de artículo: {e}")
        await update.message.reply_text("Hubo un problema iniciando la generación del artículo.")
        return ConversationHandler.END

# Manejar el tema proporcionado por el usuario
async def handle_tema(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generar artículo basado en el tema proporcionado"""
    try:
        # Obtener el tema del mensaje
        tema = update.message.text.strip()
        
        # Cancelar si el usuario no quiere continuar
        if tema.lower() == '/cancelar':
            await update.message.reply_text("Generación de artículo cancelada.")
            return ConversationHandler.END
        
        # Generar el artículo
        articulo = generar_articulo(tema if tema != '/generar' else None)
        
        if not articulo:
            await update.message.reply_text("No se pudo generar el artículo. Por favor, intenta de nuevo.")
            return ConversationHandler.END
        
        # Almacenar el artículo en el contexto de la conversación
        context.user_data['articulo'] = articulo
        
        # Crear botones de aprobación
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data='aprobar'),
                InlineKeyboardButton("✏️ Editar", callback_data='editar'),
                InlineKeyboardButton("❌ Rechazar", callback_data='rechazar')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Mostrar el artículo generado con botones de acción
        await update.message.reply_text(
            f"🤖 Artículo Generado:\n\n{articulo}\n\n"
            "Por favor, elige una acción:",
            reply_markup=reply_markup
        )
        
        return APPROVE
    
    except Exception as e:
        logging.error(f"Error al manejar tema del artículo: {e}")
        await update.message.reply_text("Hubo un problema procesando tu solicitud.")
        return ConversationHandler.END

# Manejar las acciones de los botones
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Manejar las acciones de aprobación, edición o rechazo"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Recuperar el artículo generado
        articulo = context.user_data.get('articulo')
        
        if not articulo:
            await query.edit_message_text("El artículo no está disponible. Por favor, genera uno nuevo.")
            return ConversationHandler.END
        
        if query.data == 'aprobar':
            # Publicar el artículo
            await publicar_articulo(context, articulo)
            await query.edit_message_text("✅ Artículo aprobado y publicado exitosamente.")
            return ConversationHandler.END
        
        elif query.data == 'editar':
            # Solicitar edición al usuario
            await query.edit_message_text(
                "✏️ Edita el artículo. Envía tu versión modificada:"
            )
            return EDIT
        
        elif query.data == 'rechazar':
            await query.edit_message_text("❌ Artículo rechazado. Puedes generar uno nuevo.")
            return ConversationHandler.END
    
    except Exception as e:
        logging.error(f"Error al procesar botón: {e}")
        await query.edit_message_text("Hubo un problema procesando tu selección.")
        return ConversationHandler.END

# Manejar la edición del artículo
async def editar_articulo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Manejar la edición del artículo por parte del usuario"""
    try:
        # Obtener el artículo editado
        articulo_editado = update.message.text.strip()
        
        # Crear botones de aprobación para el artículo editado
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data='aprobar'),
                InlineKeyboardButton("❌ Rechazar", callback_data='rechazar')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Mostrar el artículo editado con botones de acción
        await update.message.reply_text(
            f"🤖 Artículo Editado:\n\n{articulo_editado}\n\n"
            "Por favor, elige una acción:",
            reply_markup=reply_markup
        )
        
        # Almacenar el artículo editado
        context.user_data['articulo'] = articulo_editado
        
        return APPROVE
    
    except Exception as e:
        logging.error(f"Error al editar artículo: {e}")
        await update.message.reply_text("Hubo un problema editando el artículo.")
        return ConversationHandler.END

# Cancelar el proceso de generación
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancelar el proceso de generación de artículos"""
    await update.message.reply_text("Proceso de generación de artículos cancelado.")
    return ConversationHandler.END

# Manejar mensajes generales
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar mensajes que no son comandos"""
    try:
        # Mensaje de ayuda para usuarios que no usan comandos específicos
        await update.message.reply_text(
            "🤖 Usa los siguientes comandos:\n"
            "/start - Iniciar el bot\n"
            "/help - Mostrar ayuda\n"
            "/generar - Crear un nuevo artículo"
        )
    except Exception as e:
        logging.error(f"Error al procesar mensaje: {e}")
        await update.message.reply_text("Lo siento, hubo un error procesando tu mensaje.")

# Configuración de la aplicación FastAPI
app = FastAPI()

# Inicializar la aplicación de Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Configurar manejadores
def setup_handlers():
    # Configurar el manejador de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('generar', generar_y_enviar)],
        states={
            GENERATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tema)],
            EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_articulo)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    # Agregar manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

# Configurar manejadores al iniciar
setup_handlers()

# Endpoint de health check para Render
@app.get("/")
async def health_check():
    return {"status": "ok"}

# Endpoint para recibir actualizaciones de webhook
@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Obtener los datos JSON de la solicitud
        update_data = await request.json()
        logging.info(f"Datos recibidos: {update_data}")
        
        # Crear el objeto Update
        update = Update.de_json(update_data, application.bot)
        
        # Procesar la actualización directamente
        if update.message:
            await update.message.reply_text("¡Hola! Estoy procesando tu mensaje...")
            
            # Reenviar al manejador de mensajes
            if update.message.text and update.message.text.startswith('/'):
                await application.process_update(update)
            else:
                # Si no es un comando, usar el manejador de mensajes
                await handle_message(update, None)
        
        # Procesar otros tipos de actualizaciones
        elif update.callback_query:
            await application.process_update(update)
        
        return {"status": "ok"}
        
    except Exception as e:
        logging.error(f"Error en webhook: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

# Configurar el webhook
async def set_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("La variable de entorno WEBHOOK_URL no está configurada")
    
    webhook_url = f"{webhook_url}/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook configurado en: {webhook_url}")
    return True

# Configuración del webhook
@app.on_event("startup")
async def startup_event():
    try:
        logging.info("Iniciando aplicación FastAPI...")
        await set_webhook()
        logging.info("Aplicación lista para recibir peticiones")
    except Exception as e:
        logging.error(f"Error al iniciar la aplicación: {e}", exc_info=True)
        raise

# Función principal para iniciar la aplicación
def main():
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Obtener el puerto de la variable de entorno o usar 8000 por defecto
    port = int(os.getenv('PORT', 8000))
    
    # Iniciar el servidor FastAPI
    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == '__main__':
    main()