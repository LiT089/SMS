from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")  # Tu correo remitente (Gmail)
EMAIL_PASS = os.getenv("EMAIL_PASS")  # Contraseña de aplicación Gmail

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Correo destino que podrá cambiar desde la app
correo_destino_actual = "rangeltrejoadamarimildred@gmail.com"

# Función para enviar correo
def enviar_correo(numero, texto, destino, fecha_recepcion=None, numero_destino_netelip=None):
    if not EMAIL_USER or not EMAIL_PASS:
        logging.error("Faltan credenciales EMAIL_USER y EMAIL_PASS")
        return False

    asunto = f"📩 Respuesta SMS de {numero}"
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

# Endpoint para que la app cambie el correo destino
@app.route("/set-email", methods=["POST"])
def set_email():
    global correo_destino_actual
    data = request.get_json()
    nuevo_correo = data.get("email")

    if not nuevo_correo:
        return jsonify({"status": "error", "message": "Falta email"}), 400

    correo_destino_actual = nuevo_correo
    logging.info(f"Correo destino cambiado a: {correo_destino_actual}")
    return jsonify({"status": "ok", "message": f"Correo destino actualizado a {correo_destino_actual}"}), 200

# Endpoint que Netelip usará para mandar los SMS recibidos
@app.route("/respuesta-sms", methods=["POST"])
def recibir_sms():
    fecha = request.form.get("date")
    numero_remitente = request.form.get("from")
    numero_destino = request.form.get("destination")
    mensaje = request.form.get("message")

    logging.info(f"SMS recibido de {numero_remitente}: {mensaje}")

    if not numero_remitente or not mensaje:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    if enviar_correo(numero_remitente, mensaje, correo_destino_actual, fecha, numero_destino):
        return jsonify({"status": "ok", "message": "Correo reenviado"}), 200
    else:
        return jsonify({"status": "error", "message": "Fallo al enviar correo"}), 500

@app.route("/", methods=["GET"])
def home():
    return "Servidor de recepción SMS activo", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
