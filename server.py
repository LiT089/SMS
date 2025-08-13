from flask import Flask, request, jsonify # Importar jsonify para respuestas JSON
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging # Importar el módulo logging

# Configurar el logging básico para ver mensajes en la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener credenciales de correo de las variables de entorno
# Asegúrate de que EMAIL_USER y EMAIL_PASS estén definidos en tu archivo .env
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
# Correo por defecto al que se enviarán las respuestas si no se especifica otro
DEFAULT_DESTINATION_EMAIL = os.getenv("DEFAULT_DESTINATION_EMAIL", "rangeltrejoadamarimildred@gmail.com")

# Validar que las credenciales de correo existan
if not EMAIL_USER or not EMAIL_PASS:
    logging.error("Las variables de entorno EMAIL_USER o EMAIL_PASS no están configuradas. El envío de correos fallará.")
    # Considera salir o manejar este error de forma más robusta en un entorno de producción
    # sys.exit(1) # Descomentar para salir si las credenciales no están

app = Flask(__name__)

@app.route("/respuesta-sms", methods=["POST"])
def recibir_respuesta():
    """
    Endpoint para recibir las respuestas de SMS a través de un webhook POST.
    Netelip debería enviar aquí el contenido del SMS de respuesta.
    """
    logging.info("Petición POST recibida en /respuesta-sms")

    # Obtener los datos de la petición. Se intenta como JSON y se usa request.form como alternativa.
    data = {}
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form
    except Exception as e:
        logging.error(f"Error al obtener datos de la petición: {e}")
        return jsonify({"status": "error", "message": "Formato de datos inválido"}), 400

    logging.info(f"Datos recibidos: {data}")

    # Extraer el número del remitente y el texto del mensaje
    # CORRECCIÓN: Según tu documentación, la clave para el mensaje es 'message'.
    numero_remitente = data.get("from")
    texto_mensaje = data.get("message")

    # Determinar el correo de destino.
    correo_destino = DEFAULT_DESTINATION_EMAIL # Usar solo el valor por defecto/variable de entorno

    # Validar que los datos esenciales estén presentes
    if not numero_remitente or not texto_mensaje:
        logging.warning(f"Datos incompletos en el payload. 'from': {numero_remitente}, 'message': {texto_mensaje}")
        return jsonify({"status": "error", "message": "Datos incompletos: 'from' o 'message' faltan"}), 400

    # Enviar el correo electrónico
    success = enviar_correo(numero_remitente, texto_mensaje, correo_destino)

    if success:
        return jsonify({"status": "ok", "message": "Respuesta reenviada a correo"}), 200
    else:
        return jsonify({"status": "error", "message": "Fallo al reenviar respuesta a correo"}), 500

def enviar_correo(numero, texto, destino):
    """
    Envía un correo electrónico con la respuesta del SMS.
    Retorna True si el envío fue exitoso, False en caso contrario.
    """
    asunto = f"📩 Respuesta SMS de {numero}"
    cuerpo = f"Mensaje recibido desde el número {numero}:\n\n{texto}"

    msg = MIMEText(cuerpo)
    msg["Subject"] = asunto
    msg["From"] = EMAIL_USER
    msg["To"] = destino

    try:
        # Conexión segura a Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS) # Iniciar sesión con las credenciales
            server.sendmail(EMAIL_USER, destino, msg.as_string()) # Enviar el correo
        logging.info(f"Correo enviado con éxito a {destino} desde {numero}")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error("Error de autenticación SMTP. Verifica EMAIL_USER y EMAIL_PASS (especialmente si usas contraseñas de aplicación).")
        return False
    except smtplib.SMTPConnectError as e:
        logging.error(f"Error de conexión SMTP: {e}. Verifica tu conexión a internet o la configuración del servidor SMTP.")
        return False
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado al enviar el correo: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar la aplicación Flask.
    # En un entorno de producción, usarías un servidor WSGI como Gunicorn o uWSGI.
    logging.info("Iniciando servidor Flask en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True es útil para desarrollo
