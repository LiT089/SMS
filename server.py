from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import logging

# --- Configuración ---
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")  # Tu correo remitente
EMAIL_PASS = os.getenv("EMAIL_PASS")  # Contraseña o App Password de Gmail
CORREO_FILE = "correo_destino.txt"

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- Funciones ---
def leer_correo_destino():
    """Lee el correo destino desde archivo, si no existe usa uno por defecto."""
    if os.path.exists(CORREO_FILE):
        with open(CORREO_FILE, "r") as f:
            return f.read().strip()
    return "rangeltrejoadamarimildred@gmail.com"

def guardar_correo_destino(correo):
    """Guarda el correo destino en archivo."""
    with open(CORREO_FILE, "w") as f:
        f.write(correo)

def enviar_correo(numero, texto, destino, fecha_recepcion=None, numero_destino_netelip=None):
    """Envía el correo con los datos recibidos del SMS."""
    if not EMAIL_USER or not EMAIL_PASS:
        logging.error("Faltan credenciales EMAIL_USER y EMAIL_PASS")
        return False

    asunto = f" Respuesta SMS de {numero}"
    cuerpo = f"Mensaje recibido desde {numero}:\n\n"
    if fecha_recepcion:
        cuerpo += f"Fecha de recepción: {fecha_recepcion}\n"
    if numero_destino_netelip:
        cuerpo += f"Recibido en: {numero_destino_netelip}\n"
    cuerpo += f"\nContenido:\n{texto}"

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
        logging.error(f"Error al enviar correo: {e}")
        return False

# --- Endpoints ---
@app.route("/set-email", methods=["POST"])
def set_email():
    """Cambia el correo destino desde la app."""
    data = request.get_json()
    nuevo_correo = data.get("email")

    if not nuevo_correo or "@" not in nuevo_correo:
        return jsonify({"status": "error", "message": "Correo inválido"}), 400

    guardar_correo_destino(nuevo_correo)
    logging.info(f"Correo destino cambiado a: {nuevo_correo}")
    return jsonify({"status": "ok", "message": f"Correo destino actualizado a {nuevo_correo}"}), 200

@app.route("/respuesta-sms", methods=["POST"])
def recibir_sms():
    """Netelip envía aquí los SMS recibidos."""
    fecha = request.form.get("date")
    numero_remitente = request.form.get("from")
    numero_destino = request.form.get("destination")
    mensaje = request.form.get("message")

    logging.info(f"SMS recibido de {numero_remitente}: {mensaje}")

    if not numero_remitente or not mensaje:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    correo_destino_actual = leer_correo_destino()
    if enviar_correo(numero_remitente, mensaje, correo_destino_actual, fecha, numero_destino):
        return jsonify({"status": "ok", "message": "Correo reenviado"}), 200
    else:
        return jsonify({"status": "error", "message": "Fallo al enviar correo"}), 500

@app.route("/", methods=["GET"])
def home():
    return "Servidor de recepción SMS activo", 200

# --- Inicio ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



