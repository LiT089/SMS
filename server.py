from flask import Flask, request, jsonify
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cargar variables de entorno
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Correo destino editable en tiempo real
DEFAULT_DESTINATION_EMAIL = os.getenv("DEFAULT_DESTINATION_EMAIL", "eduardo.rangel@loomsys.com.mx")

if not EMAIL_USER or not EMAIL_PASS:
    logging.error("Faltan EMAIL_USER o EMAIL_PASS. El envío de correos fallará.")

app = Flask(__name__)

@app.route("/respuesta-sms", methods=["POST"])
def recibir_respuesta():
    logging.info("POST recibido en /respuesta-sms")

    data = request.json if request.is_json else request.form
    logging.info(f"Datos recibidos: {data}")

    numero_remitente = data.get("from")
    texto_mensaje = data.get("message")

    if not numero_remitente or not texto_mensaje:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    success = enviar_correo(numero_remitente, texto_mensaje, DEFAULT_DESTINATION_EMAIL)

    return (
        jsonify({"status": "ok", "message": "Correo enviado"}) if success
        else jsonify({"status": "error", "message": "Fallo al enviar correo"}), 200 if success else 500
    )

@app.route("/config-email", methods=["POST"])
def configurar_correo():
    global DEFAULT_DESTINATION_EMAIL
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"status": "error", "message": "Falta el campo 'email'"}), 400
    DEFAULT_DESTINATION_EMAIL = data["email"]
    logging.info(f"Correo destino cambiado a: {DEFAULT_DESTINATION_EMAIL}")
    return jsonify({"status": "ok", "message": f"Correo destino cambiado a {DEFAULT_DESTINATION_EMAIL}"}), 200

def enviar_correo(numero, texto, destino):
    asunto = f"Respuesta SMS de {numero}"
    cuerpo = f"Mensaje recibido desde el número {numero}:\n\n{texto}"
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


