from flask import Flask, request, jsonify
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging

# Configurar el logging para ver los mensajes en Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno (solo funciona en local, Render las manejará directamente)
load_dotenv()

# Obtener credenciales de correo de las variables de entorno
# Render nos permitirá configurar EMAIL_USER y EMAIL_PASS de manera segura.
#
# Importante: Estas credenciales son del correo que USARÁ EL SERVIDOR PARA ENVIAR
# los correos. El correo del destinatario (el de tu jefe) se establece más abajo.
#
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Verificar si las credenciales de correo existen
if not EMAIL_USER or not EMAIL_PASS:
    logging.error("Las variables de entorno EMAIL_USER o EMAIL_PASS no están configuradas.")
    # El servidor continuará, pero el envío de correos fallará si no están configuradas en Render.

app = Flask(__name__)

# --- Función para enviar correo ---
def enviar_correo(numero, texto, destino, fecha_recepcion=None, numero_destino_netelip=None):
    """
    Envía un correo electrónico con la respuesta del SMS.
    Retorna True si el envío fue exitoso, False en caso contrario.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        logging.error("No se puede enviar correo: Credenciales de correo no configuradas.")
        return False
        
    asunto = f"📩 Respuesta SMS de {numero}"
    cuerpo = f"Mensaje recibido desde el número {numero}:\n\n"
    if fecha_recepcion:
        cuerpo += f"Fecha de recepción: {fecha_recepcion}\n"
    if numero_destino_netelip:
        cuerpo += f"Recibido en tu número Netelip: {numero_destino_netelip}\n"
    cuerpo += f"\nContenido del mensaje:\n{texto}"

    msg = MIMEText(cuerpo)
    msg["Subject"] = asunto
    msg["From"] = EMAIL_USER
    msg["To"] = destino

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, destino, msg.as_string())
        logging.info(f"Correo enviado con éxito a {destino} desde {numero}")
        return True
    except Exception as e:
        logging.error(f"Ocurrió un error al enviar el correo: {e}")
        return False

# --- Endpoint para el webhook ---
@app.route("/respuesta-sms", methods=["POST"])
def recibir_respuesta():
    logging.info("Petición POST recibida en /respuesta-sms")

    # Obtener los datos del webhook de Netelip (form-data)
    fecha_recepcion = request.form.get("date")
    numero_remitente = request.form.get("from")
    numero_destino_netelip = request.form.get("destination")
    texto_mensaje = request.form.get("message")

    logging.info(f"Datos recibidos: From={numero_remitente}, Message={texto_mensaje}")

    correo_destino = request.args.get("email")
    if not correo_destino:
        logging.warning("No se encontró el parámetro 'email' en la URL. Usando correo por defecto.")
        # Usamos el correo de tu jefe como valor por defecto si no se especifica otro
        correo_destino = "eduardo.rangel@loomsys.com.mx"

    if not numero_remitente or not texto_mensaje:
        logging.warning("Datos incompletos en el webhook. 'from' o 'message' faltan.")
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    success = enviar_correo(numero_remitente, texto_mensaje, correo_destino, fecha_recepcion, numero_destino_netelip)

    if success:
        return jsonify({"status": "ok", "message": "Respuesta reenviada a correo"}), 200
    else:
        return jsonify({"status": "error", "message": "Fallo al reenviar respuesta a correo"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
