from flask import Flask, request, jsonify
import smtplib
import os
import json
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
CONFIG_KEY = os.getenv("CONFIG_KEY", "12345")  # clave de seguridad para cambiar el correo

# Archivo para guardar el correo destino
EMAIL_CONFIG_FILE = "email_config.json"

# Funciones para leer/guardar correo destino
def get_email_destino():
    if os.path.exists(EMAIL_CONFIG_FILE):
        with open(EMAIL_CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("email", "eduardo.rangel@loomsys.com.mx")
    return "eduardo.rangel@loomsys.com.mx"

def set_email_destino(email):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump({"email": email}, f)

# Inicializar Flask
app = Flask(__name__)

# Función para enviar correo
def enviar_correo(numero, texto, destino, fecha_recepcion=None, numero_destino_netelip=None):
    if not EMAIL_USER or not EMAIL_PASS:
        logging.error("Credenciales de correo no configuradas.")
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
        logging.info(f"Correo enviado a {destino}")
        return True
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")
        return False

# Endpoint para recibir SMS desde Netelip
@app.route("/respuesta-sms", methods=["POST"])
def recibir_respuesta():
    fecha_recepcion = request.form.get("date")
    numero_remitente = request.form.get("from")
    numero_destino_netelip = request.form.get("destination")
    texto_mensaje = request.form.get("message")

    logging.info(f"SMS recibido: From={numero_remitente}, Msg={texto_mensaje}")

    if not numero_remitente or not texto_mensaje:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    correo_destino = get_email_destino()

    if enviar_correo(numero_remitente, texto_mensaje, correo_destino, fecha_recepcion, numero_destino_netelip):
        return jsonify({"status": "ok", "message": f"Respuesta reenviada a {correo_destino}"}), 200
    else:
        return jsonify({"status": "error", "message": "Fallo al enviar correo"}), 500

# Endpoint para cambiar el correo destino
@app.route("/config-email", methods=["POST"])
def configurar_email():
    auth_key = request.args.get("key")
    if auth_key != CONFIG_KEY:
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    nuevo_email = data.get("email")

    if not nuevo_email:
        return jsonify({"status": "error", "message": "Falta el campo 'email'"}), 400

    set_email_destino(nuevo_email)
    logging.info(f"Correo destino actualizado a: {nuevo_email}")
    return jsonify({"status": "ok", "message": f"Correo actualizado a {nuevo_email}"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
