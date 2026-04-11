from __future__ import print_function
from flask import Flask, request, jsonify
import base64
from email.mime.text import MIMEText
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
app = Flask(__name__)

# ===================== AUTENTICACIÓN =====================
def authenticate_gmail():
    creds = None
    if os.path.exists('confidencial/token.pickle'):
        with open('confidencial/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('confidencial/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('confidencial/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

# ===================== FUNCIONES DE MENSAJES =====================
def create_message_text(sender, to, subject, message_text):
    """Crea un mensaje de texto plano"""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw_message.decode()}

def create_message_html(sender, to, subject, html_content):
    """Crea un mensaje HTML"""
    message = MIMEText(html_content, "html")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw_message.decode()}

def send_message(service, user_id, message):
    """Envía el mensaje usando la API de Gmail"""
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        return {
            'success': True,
            'message_id': sent_message['id'],
            'status': 'Mensaje enviado exitosamente'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status': f'Error al enviar: {e}'
        }

# ===================== ENDPOINTS =====================

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de salud para verificar que la API está activa"""
    return jsonify({'status': 'API activa', 'message': 'Servicio de notificaciones disponible'}), 200

@app.route('/api/enviar-texto-plano', methods=['POST'])
def enviar_texto_plano():
    """
    Endpoint para enviar correo de texto plano
    JSON esperado:
    {
        "nombre": "Juan",
        "destinatario": "juan@example.com",
        "remitente": "tu-email@gmail.com",
        "asunto": "Asunto del correo",
        "contenido": "Contenido del correo"
    }
    """
    try:
        datos = request.get_json()
        
        # Validar datos requeridos
        if not all(key in datos for key in ['nombre', 'destinatario', 'remitente', 'asunto', 'contenido']):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos: nombre, destinatario, remitente, asunto, contenido'
            }), 400
        
        nombre = datos['nombre']
        destinatario = datos['destinatario']
        remitente = datos['remitente']
        asunto = datos['asunto']
        contenido = datos['contenido']
        
        # Reemplazar nombre en el contenido si está disponible
        contenido_procesado = contenido.replace('[Nombre]', nombre).replace('[Nombre del Usuario]', nombre)
        
        # Autenticar y crear servicio
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        
        # Crear y enviar mensaje
        mensaje = create_message_text(remitente, destinatario, asunto, contenido_procesado)
        resultado = send_message(service, 'me', mensaje)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Error en el servidor'
        }), 500

@app.route('/api/enviar-html', methods=['POST'])
def enviar_html():
    """
    Endpoint para enviar correo HTML con plantilla
    JSON esperado:
    {
        "nombre": "Juan",
        "destinatario": "juan@example.com",
        "remitente": "tu-email@gmail.com",
        "asunto": "Bienvenido a KALA Buses"
    }
    """
    try:
        datos = request.get_json()
        
        # Validar datos requeridos
        if not all(key in datos for key in ['nombre', 'destinatario', 'remitente', 'asunto']):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos: nombre, destinatario, remitente, asunto'
            }), 400
        
        nombre = datos['nombre']
        destinatario = datos['destinatario']
        remitente = datos['remitente']
        asunto = datos['asunto']
        
        # Cargar y procesar plantilla HTML
        try:
            with open("plantilla_registro.html", "r", encoding="utf-8") as archivo:
                html_template = archivo.read()
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'Archivo plantilla_registro.html no encontrado'
            }), 400
        
        # Reemplazar variables en la plantilla
        html_procesado = html_template.replace('[Nombre del Usuario]', nombre).replace('[Nombre]', nombre)
        
        # Autenticar y crear servicio
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        
        # Crear y enviar mensaje
        mensaje = create_message_html(remitente, destinatario, asunto, html_procesado)
        resultado = send_message(service, 'me', mensaje)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Error en el servidor'
        }), 500

@app.route('/api/enviar-multiples', methods=['POST'])
def enviar_multiples():
    """
    Endpoint para enviar correo a múltiples destinatarios
    JSON esperado:
    {
        "nombre": "Juan",
        "destinatarios": "email1@example.com,email2@example.com",
        "remitente": "tu-email@gmail.com",
        "asunto": "Asunto del correo",
        "contenido": "Contenido del correo"
    }
    """
    try:
        datos = request.get_json()
        
        # Validar datos requeridos
        if not all(key in datos for key in ['nombre', 'destinatarios', 'remitente', 'asunto', 'contenido']):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos: nombre, destinatarios, remitente, asunto, contenido'
            }), 400
        
        nombre = datos['nombre']
        destinatarios = datos['destinatarios']  # Separados por coma
        remitente = datos['remitente']
        asunto = datos['asunto']
        contenido = datos['contenido']
        
        # Reemplazar nombre en el contenido
        contenido_procesado = contenido.replace('[Nombre]', nombre).replace('[Nombre del Usuario]', nombre)
        
        # Autenticar y crear servicio
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        
        # Enviar a cada destinatario
        resultados = []
        for destinatario in destinatarios.split(','):
            destinatario = destinatario.strip()
            mensaje = create_message_text(remitente, destinatario, asunto, contenido_procesado)
            resultado = send_message(service, 'me', mensaje)
            resultados.append({
                'destinatario': destinatario,
                'resultado': resultado
            })
        
        # Verificar si todos fueron exitosos
        todos_exitosos = all(r['resultado']['success'] for r in resultados)
        
        return jsonify({
            'success': todos_exitosos,
            'total_destinatarios': len(resultados),
            'resultados': resultados,
            'status': 'Correos procesados'
        }), 200 if todos_exitosos else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Error en el servidor'
        }), 500

@app.route('/api/enviar-codigo-verificacion', methods=['POST'])
def enviar_codigo_verificacion():
    """
    Endpoint para enviar correo con código de verificación
    JSON esperado:
    {
        "nombre": "Juan",
        "destinatario": "juan@example.com",
        "remitente": "tu-email@gmail.com",
        "asunto": "Código de Verificación - KALA Buses",
        "codigo": "123456"
    }
    """
    try:
        datos = request.get_json()
        
        # Validar datos requeridos
        if not all(key in datos for key in ['nombre', 'destinatario', 'remitente', 'asunto', 'codigo']):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos: nombre, destinatario, remitente, asunto, codigo'
            }), 400
        
        nombre = datos['nombre']
        destinatario = datos['destinatario']
        remitente = datos['remitente']
        asunto = datos['asunto']
        codigo = datos['codigo']
        
        # Cargar y procesar plantilla HTML
        try:
            with open("plantilla_codigo_verificacion.html", "r", encoding="utf-8") as archivo:
                html_template = archivo.read()
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'Archivo plantilla_codigo_verificacion.html no encontrado'
            }), 400
        
        # Reemplazar variables en la plantilla
        html_procesado = html_template.replace('[Nombre del Usuario]', nombre).replace('[CODIGO_VERIFICACION]', codigo)
        
        # Autenticar y crear servicio
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        
        # Crear y enviar mensaje
        mensaje = create_message_html(remitente, destinatario, asunto, html_procesado)
        resultado = send_message(service, 'me', mensaje)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Error en el servidor'
        }), 500

@app.route('/api/enviar-cambio-contrasena', methods=['POST'])
def enviar_cambio_contrasena():
    """
    Endpoint para enviar correo de cambio de contraseña
    JSON esperado:
    {
        "nombre": "Juan",
        "destinatario": "juan@example.com",
        "remitente": "tu-email@gmail.com",
        "asunto": "Cambiar tu Contraseña - KALA Buses",
        "urlCambio": "https://sistema.com/reset-password?token=xxxxx",
        "tiempoValidez": "30 minutos"
    }
    """
    try:
        datos = request.get_json()
        
        # Validar datos requeridos
        if not all(key in datos for key in ['nombre', 'destinatario', 'remitente', 'asunto', 'urlCambio', 'tiempoValidez']):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos: nombre, destinatario, remitente, asunto, urlCambio, tiempoValidez'
            }), 400
        
        nombre = datos['nombre']
        destinatario = datos['destinatario']
        remitente = datos['remitente']
        asunto = datos['asunto']
        url_cambio = datos['urlCambio']
        tiempo_validez = datos['tiempoValidez']
        
        # Cargar y procesar plantilla HTML
        try:
            with open("plantilla_cambio_contrasena.html", "r", encoding="utf-8") as archivo:
                html_template = archivo.read()
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'Archivo plantilla_cambio_contrasena.html no encontrado'
            }), 400
        
        # Reemplazar variables en la plantilla
        html_procesado = html_template.replace('[Nombre del Usuario]', nombre) \
                                      .replace('[URL_CAMBIO_CONTRASENA]', url_cambio) \
                                      .replace('[TIEMPO_VALIDEZ]', tiempo_validez)
        
        # Autenticar y crear servicio
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        
        # Crear y enviar mensaje
        mensaje = create_message_html(remitente, destinatario, asunto, html_procesado)
        resultado = send_message(service, 'me', mensaje)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'Error en el servidor'
        }), 500

@app.route('/api/endpoints', methods=['GET'])
def listar_endpoints():
    """Lista todos los endpoints disponibles"""
    return jsonify({
        'endpoints': [
            {
                'nombre': 'Health Check',
                'metodo': 'GET',
                'url': '/api/health',
                'descripcion': 'Verifica si la API está activa'
            },
            {
                'nombre': 'Enviar Texto Plano',
                'metodo': 'POST',
                'url': '/api/enviar-texto-plano',
                'parametros': ['nombre', 'destinatario', 'remitente', 'asunto', 'contenido']
            },
            {
                'nombre': 'Enviar HTML',
                'metodo': 'POST',
                'url': '/api/enviar-html',
                'parametros': ['nombre', 'destinatario', 'remitente', 'asunto']
            },
            {
                'nombre': 'Enviar Código de Verificación',
                'metodo': 'POST',
                'url': '/api/enviar-codigo-verificacion',
                'parametros': ['nombre', 'destinatario', 'remitente', 'asunto', 'codigo']
            },
            {
                'nombre': 'Enviar a Múltiples',
                'metodo': 'POST',
                'url': '/api/enviar-multiples',
                'parametros': ['nombre', 'destinatarios', 'remitente', 'asunto', 'contenido']
            },
            {
                'nombre': 'Enviar Cambio de Contraseña',
                'metodo': 'POST',
                'url': '/api/enviar-cambio-contrasena',
                'parametros': ['nombre', 'destinatario', 'remitente', 'asunto', 'urlCambio', 'tiempoValidez']
            }
        ]
    }), 200

# ===================== MANEJO DE ERRORES =====================
@app.errorhandler(404)
def no_encontrado(error):
    return jsonify({
        'error': 'Endpoint no encontrado',
        'sugerencia': 'Usa GET /api/endpoints para ver los endpoints disponibles'
    }), 404

@app.errorhandler(405)
def metodo_no_permitido(error):
    return jsonify({
        'error': 'Método HTTP no permitido'
    }), 405

if __name__ == '__main__':
    app.run(debug=True, port=5000)
