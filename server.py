from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import logging

# --- Configuración ---
load_dotenv()

# Credenciales para el envío de correos
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Archivo para persistir el correo destino
CORREO_FILE = "correo_destino.txt"

# Configuración de logging para ver la actividad del servidor
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Funciones de Ayuda ---
def leer_correo_destino():
    """Lee el correo destino desde el archivo. Si no existe, usa uno por defecto."""
    try:
        if os.path.exists(CORREO_FILE):
            with open(CORREO_FILE, "r") as f:
                return f.read().strip()
    except Exception as e:
        logging.error(f"Error al leer el archivo de correo: {e}")
    # Correo por defecto si el archivo no existe o falla la lectura
    return "tu_correo_por_defecto@ejemplo.com"

def guardar_correo_destino(correo):
    """Guarda el nuevo correo destino en el archivo."""
    try:
        with open(CORREO_FILE, "w") as f:
            f.write(correo)
        return True
    except Exception as e:
        logging.error(f"Error al guardar el archivo de correo: {e}")
        return False

def enviar_correo(numero_remitente, texto_sms, correo_destino, fecha_recepcion=None, numero_netelip=None):
    """Construye y envía el correo electrónico con la respuesta del SMS."""
    if not EMAIL_USER or not EMAIL_PASS:
        logging.error("Credenciales de correo (EMAIL_USER, EMAIL_PASS) no configuradas en .env")
        return False

    asunto = f"Respuesta SMS de {numero_remitente}"
    cuerpo = f"Has recibido una nueva respuesta a un SMS:\n\n"
    cuerpo += f"De: {numero_remitente}\n"
    if fecha_recepcion:
        cuerpo += f"Fecha: {fecha_recepcion}\n"
    if numero_netelip:
        cuerpo += f"Recibido en el número: {numero_netelip}\n"
    cuerpo += "----------------------------------------\n"
    cuerpo += f"Mensaje:\n{texto_sms}\n"
    cuerpo += "----------------------------------------\n"

    msg = MIMEText(cuerpo)
    msg["Subject"] = asunto
    msg["From"] = f"Alertas SMS <{EMAIL_USER}>"
    msg["To"] = correo_destino

    try:
        # Conexión segura con el servidor SMTP de Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, correo_destino, msg.as_string())
        logging.info(f"Correo de respuesta de {numero_remitente} enviado exitosamente a {correo_destino}")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error("Error de autenticación con Gmail. Revisa EMAIL_USER y EMAIL_PASS (quizás necesites una App Password).")
        return False
    except Exception as e:
        logging.error(f"Error inesperado al enviar correo: {e}")
        return False

# --- Endpoints de la API ---
@app.route("/set-email", methods=["POST"])
def set_email():
    """
    Endpoint PÚBLICO para cambiar el correo destino.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Petición inválida, se esperaba JSON."}), 400

    nuevo_correo = data.get("email")

    if not nuevo_correo or "@" not in nuevo_correo:
        return jsonify({"status": "error", "message": "Formato de correo inválido."}), 400

    if guardar_correo_destino(nuevo_correo):
        logging.info(f"Correo destino actualizado a: {nuevo_correo}")
        return jsonify({"status": "ok", "message": f"Correo destino actualizado a {nuevo_correo}"}), 200
    else:
        return jsonify({"status": "error", "message": "No se pudo guardar el correo en el servidor."}), 500


@app.route("/respuesta-sms", methods=["POST"])
def recibir_sms():
    """
    Endpoint público que Netelip usará para notificar respuestas de SMS.
    """
    # Netelip envía los datos como 'form-data'
    fecha = request.form.get("date")
    numero_remitente = request.form.get("from")
    numero_destino_netelip = request.form.get("destination")
    mensaje = request.form.get("message")

    logging.info(f"SMS recibido de {numero_remitente} para {numero_destino_netelip}: '{mensaje}'")

    if not numero_remitente or not mensaje:
        logging.error("Petición de Netelip con datos incompletos.")
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    correo_destino_actual = leer_correo_destino()
    
    if enviar_correo(numero_remitente, mensaje, correo_destino_actual, fecha, numero_destino_netelip):
        # Se responde 'ok' a Netelip para que sepa que lo hemos procesado
        return jsonify({"status": "ok", "message": "Correo reenviado"}), 200
    else:
        # Se responde con error si no pudimos enviar el email
        return jsonify({"status": "error", "message": "Fallo interno al enviar correo"}), 500


@app.route("/", methods=["GET"])
def home():
    """Endpoint de 'health check' para saber si el servidor está activo."""
    return "Servidor de recepción SMS activo y funcionando.", 200

# --- Inicio del Servidor ---
if __name__ == "__main__":
    # Render y otros servicios de hosting proporcionan la variable PORT
    port = int(os.environ.get("PORT", 5000))
    # 'host="0.0.0.0"' es crucial para que sea accesible desde fuera del contenedor
    app.run(host="0.0.0.0", port=port)




