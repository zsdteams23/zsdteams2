import discord
from discord.ext import commands
import re
import unicodedata

# Token del bot (recuerda reemplazarlo por tu token real)
TOKEN = "MTM0MTE1MzQ0MzA1ODAyNDQ4OQ.GmqvYK.P9gGFpE6hjB74jySHkv4rz5gu2cE5js3RIDYBE"  # Tu token real aquí

# Intenciones del bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

# Configuración del bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Expresiones regulares para detección
DISCORD_INVITE_REGEX = r"(https?:\/\/)?(www\.)?(discord\.gg\/|discord\.com\/invite\/)[\w\-]+"
STEAM_SCAM_REGEX = r"(https?:\/\/)?(www\.)?steam.*(gift|card|free|freecard|giftfree|community\.com\/gift-card\/pay\/\d+)[\w\-]*"
TELEGRAM_INVITE_REGEX = r"(https?:\/\/)?(www\.)?(t\.me\/|telegram\.me\/|telegram\.dog\/)[\w\-]+"
BLOCKED_WORDS = ["solara is back", "solara executor"]

# ID del canal de logs
LOG_CHANNEL_ID = 1291047993700782173

# Canales permitidos para invitaciones
ALLOWED_INVITE_CHANNELS = {1332801216475959416, 1332801437377364120}

def normalize_text(text):
    """Convierte texto con fuentes raras a su versión ASCII para mejor detección."""
    normalized = ''.join(
        c if unicodedata.category(c) != 'Mn' else ''
        for c in unicodedata.normalize('NFKD', text)
    )
    return ''.join(
        unicodedata.name(c).split()[-1] if c.isalnum() else c
        for c in normalized
    ).lower()

async def log_message(log_channel, content):
    """Envía mensajes al canal de logs."""
    if log_channel:
        await log_channel.send(content)

async def handle_violation(message, reason, ban_user=True):
    """Maneja violaciones detectadas: elimina mensajes, intenta banear y registra logs."""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    try:
        # Intentar eliminar el mensaje
        await message.delete()
        print(f"Mensaje eliminado de {message.author}: {message.content}")

        if ban_user:
            # Intentar banear al usuario
            await message.guild.ban(message.author, reason=reason)
            print(f"Usuario {message.author} baneado por: {reason}.")

            # Eliminar cualquier otro mensaje reciente del usuario en todos los canales
            for channel in message.guild.text_channels:
                async for msg in channel.history(limit=50):
                    if msg.author == message.author:
                        await msg.delete()

        # Registrar en el canal de logs
        if log_channel:
            await log_message(
                log_channel,
                f"⚠️ **Usuario baneado:** {message.author} (ID: {message.author.id})\n"
                f"**Motivo:** {reason}.\n"
                f"**Mensaje eliminado:** {message.content}"
            )

    except discord.Forbidden:
        print(f"No se pudo banear al usuario {message.author}.")
        if log_channel:
            await log_message(
                log_channel,
                f"⚠️ **No se pudo banear al usuario:** {message.author} (ID: {message.author.id})\n"
                f"**Motivo:** {reason}.\n"
                f"**Mensaje eliminado:** {message.content}"
            )

    except discord.HTTPException as e:
        print(f"Error HTTP al intentar manejar la violación: {e}")
        if log_channel:
            await log_message(
                log_channel,
                f"⚠️ **Error HTTP:** No se pudo procesar la violación.\n"
                f"**Usuario:** {message.author} (ID: {message.author.id})\n"
                f"**Error:** {e}"
            )

@bot.event
async def on_message(message):
    """Escucha mensajes y actúa de inmediato en violaciones."""
    if message.author == bot.user:
        return

    # 🔹 Permitir que el bot con ID 1320276882398253097 envíe invitaciones
    if message.author.id == 1320276882398253097:
        return  

    normalized_content = normalize_text(message.content)  # 🔹 Aplicar la nueva normalización

    if message.channel.id in ALLOWED_INVITE_CHANNELS:
        return

    if re.search(DISCORD_INVITE_REGEX, normalized_content):
        await handle_violation(message, "Compartir links de invitación a Discord", ban_user=True)
    elif re.search(STEAM_SCAM_REGEX, normalized_content):
        await handle_violation(message, "Compartir links sospechosos de estafas relacionadas con Steam", ban_user=True)
    elif re.search(TELEGRAM_INVITE_REGEX, normalized_content):
        await handle_violation(message, "Compartir links de invitación a Telegram", ban_user=True)
    elif any(word in normalized_content for word in BLOCKED_WORDS):
        await handle_violation(message, "Uso de palabras bloqueadas", ban_user=False)
    elif "/flood" in normalized_content:
        await handle_violation(message, "Uso del comando /flood", ban_user=True)

# Iniciar el bot
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("Error: Token inválido.")
except Exception as e:
    print(f"Error al iniciar el bot: {e}")