"""
Cliente de prueba para la API de notificaciones
Realiza pruebas a los endpoints: texto plano, HTML y múltiples destinatarios
"""

import requests
import json
from colorama import Fore, Style, init

# Inicializar colorama para colores en consola
init(autoreset=True)

# URL base de la API
BASE_URL = "http://localhost:5000"

# Configuración de remitente y destinatarios de prueba
REMITENTE = "laucagomez1615@gmail.com"
DESTINATARIO_PRINCIPAL = "laura.cardona43736@ucaldas.edu.co"
DESTINATARIOS_MULTIPLES = "laura.cardona43736@ucaldas.edu.co,felipe.buitrago@ucaldas.edu.co"

def print_header(titulo):
    """Imprime un encabezado formateado"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{titulo.center(60)}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

def print_success(mensaje):
    """Imprime un mensaje de éxito"""
    print(f"{Fore.GREEN}✅ {mensaje}{Style.RESET_ALL}")

def print_error(mensaje):
    """Imprime un mensaje de error"""
    print(f"{Fore.RED}❌ {mensaje}{Style.RESET_ALL}")

def print_info(mensaje):
    """Imprime un mensaje informativo"""
    print(f"{Fore.YELLOW}ℹ️  {mensaje}{Style.RESET_ALL}")

def test_health():
    """Prueba el endpoint de salud"""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print_success(f"API activa - Status: {response.status_code}")
            print(f"Respuesta: {json.dumps(response.json(), indent=2)}")
        else:
            print_error(f"Error - Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar a la API. ¿Está corriendo en puerto 5000?")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_listar_endpoints():
    """Prueba el endpoint que lista todos los endpoints"""
    print_header("TEST 2: Listar Endpoints")
    try:
        response = requests.get(f"{BASE_URL}/api/endpoints", timeout=5)
        if response.status_code == 200:
            print_success("Endpoints listados correctamente")
            endpoints = response.json()['endpoints']
            for ep in endpoints:
                print(f"\n  📌 {ep['nombre']} ({ep['metodo']})")
                print(f"     URL: {ep['url']}")
                if 'parametros' in ep:
                    print(f"     Parámetros: {', '.join(ep['parametros'])}")
        else:
            print_error(f"Error - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_enviar_texto_plano():
    """Prueba el endpoint para enviar texto plano"""
    print_header("TEST 3: Enviar Correo de Texto Plano")
    
    datos = {
        "nombre": "Laura García",
        "destinatario": DESTINATARIO_PRINCIPAL,
        "remitente": REMITENTE,
        "asunto": "Prueba API - Texto Plano",
        "contenido": "Hola [Nombre del Usuario],\n\nEste es un correo de prueba desde la API.\nHemos reemplazado tu nombre automáticamente en el mensaje.\n\nSaludos,\nEquipo de Notificaciones"
    }
    
    print_info(f"Enviando a: {datos['destinatario']}")
    print_info(f"Nombre para reemplazar: {datos['nombre']}")
    print(f"\nPayload:")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enviar-texto-plano",
            json=datos,
            timeout=10
        )
        
        if response.status_code == 200:
            resultado = response.json()
            if resultado['success']:
                print_success("Correo enviado exitosamente")
                print(f"ID del mensaje: {resultado['message_id']}")
            else:
                print_error(f"Error: {resultado['error']}")
        else:
            print_error(f"Error - Status: {response.status_code}")
            print(f"Respuesta: {response.text}")
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar a la API")
    except requests.exceptions.Timeout:
        print_error("Timeout - La API tardó demasiado en responder")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_enviar_html():
    """Prueba el endpoint para enviar correo HTML"""
    print_header("TEST 4: Enviar Correo HTML con Plantilla")
    
    datos = {
        "nombre": "Juan Carlos",
        "destinatario": DESTINATARIO_PRINCIPAL,
        "remitente": REMITENTE,
        "asunto": "¡Bienvenido a KALA Buses!"
    }
    
    print_info(f"Enviando a: {datos['destinatario']}")
    print_info(f"Nombre para reemplazar en plantilla: {datos['nombre']}")
    print(f"\nPayload:")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enviar-html",
            json=datos,
            timeout=10
        )
        
        if response.status_code == 200:
            resultado = response.json()
            if resultado['success']:
                print_success("Correo HTML enviado exitosamente")
                print(f"ID del mensaje: {resultado['message_id']}")
            else:
                print_error(f"Error: {resultado['error']}")
        else:
            print_error(f"Error - Status: {response.status_code}")
            print(f"Respuesta: {response.text}")
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar a la API")
    except requests.exceptions.Timeout:
        print_error("Timeout - La API tardó demasiado en responder")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_enviar_multiples():
    """Prueba el endpoint para enviar a múltiples destinatarios"""
    print_header("TEST 5: Enviar a Múltiples Destinatarios")
    
    datos = {
        "nombre": "Felipe Buitrago",
        "destinatarios": DESTINATARIOS_MULTIPLES,
        "remitente": REMITENTE,
        "asunto": "Prueba API - Múltiples Destinatarios",
        "contenido": "Hola [Nombre del Usuario],\n\nEste correo ha sido enviado a múltiples destinatarios.\nTu nombre es: [Nombre]\n\nSaludos del equipo"
    }
    
    print_info(f"Enviando a: {datos['destinatarios']}")
    print_info(f"Nombre para reemplazar: {datos['nombre']}")
    print(f"\nPayload:")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enviar-multiples",
            json=datos,
            timeout=10
        )
        
        if response.status_code == 200:
            resultado = response.json()
            if resultado['success']:
                print_success(f"Correos enviados a {resultado['total_destinatarios']} destinatarios")
                for item in resultado['resultados']:
                    if item['resultado']['success']:
                        print_success(f"  → {item['destinatario']}: {item['resultado']['message_id']}")
                    else:
                        print_error(f"  → {item['destinatario']}: {item['resultado']['error']}")
            else:
                print_error("Algunos correos no pudieron ser enviados")
                for item in resultado['resultados']:
                    print_info(f"  → {item['destinatario']}: {item['resultado']['status']}")
        else:
            print_error(f"Error - Status: {response.status_code}")
            print(f"Respuesta: {response.text}")
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar a la API")
    except requests.exceptions.Timeout:
        print_error("Timeout - La API tardó demasiado en responder")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def main():
    """Función principal para ejecutar todos los tests"""
    print(f"\n{Fore.MAGENTA}{'*'*60}")
    print(f"{Fore.MAGENTA}CLIENTE DE PRUEBA - API DE NOTIFICACIONES".center(60))
    print(f"{Fore.MAGENTA}{'*'*60}{Style.RESET_ALL}")
    
    print_info("Asegúrate de que la API está corriendo con: python app.py")
    print_info("Esperando 2 segundos antes de iniciar pruebas...\n")
    
    import time
    time.sleep(2)
    
    try:
        # Ejecutar tests
        test_health()
        test_listar_endpoints()
        test_enviar_texto_plano()
        test_enviar_html()
        test_enviar_multiples()
        
        print_header("PRUEBAS COMPLETADAS")
        print_success("Todos los tests han sido ejecutados")
        print_info("Revisa los correos en tu bandeja de entrada para verificar que se enviaron")
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Pruebas interrumpidas por el usuario{Style.RESET_ALL}")
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()
