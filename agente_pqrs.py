from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

app = Flask(__name__)

# ─────────────────────────────────────────
# 1️⃣ Contrato de salida (patrón del profesor: 4_respuestas_estructuradas.py)
# ─────────────────────────────────────────
class AnalisisPqrs(BaseModel):
    prioridad: str = Field(description="Prioridad de atención: Alta, Media o Baja")
    resumen: str = Field(description="Resumen en una sola línea de la solicitud")
    departamento_responsable: str = Field(description="Departamento que debe atender: Operaciones, Mantenimiento, Atención al Cliente o Tecnología")
    tiempo_estimado_dias: int = Field(description="Días estimados para resolver según prioridad (Alta=3, Media=7, Baja=15)")
    mensaje_ciudadano: str = Field(description="Mensaje personalizado y empático para enviarle al ciudadano explicando qué pasará con su solicitud")

# ─────────────────────────────────────────
# 2️⃣ Parser + LLM (mismo patrón del profesor)
# ─────────────────────────────────────────
parser = JsonOutputParser(pydantic_object=AnalisisPqrs)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Eres un sistema de análisis de PQRS para KALA Buses, empresa de transporte público.\n"
     "Analiza la solicitud del ciudadano y responde SOLO en el formato JSON indicado.\n\n"
     "Reglas de prioridad:\n"
     "- Alta: quejas sobre seguridad, accidentes, conductor agresivo, situaciones urgentes\n"
     "- Media: reclamos sobre servicio deficiente, rutas incorrectas, tarjetas, cobros\n"
     "- Baja: sugerencias, peticiones de información, mejoras generales\n\n"
     "Departamentos según categoría:\n"
     "- Conductor → Operaciones\n"
     "- Bus → Mantenimiento\n"
     "- Ruta → Operaciones\n"
     "- Tarjeta → Tecnología\n"
     "- Otro → Atención al Cliente\n\n"
     "{format_instructions}"),
    ("human", "Tipo de solicitud: {tipo}\nCategoría: {categoria}\nDescripción del ciudadano: {descripcion}")
])

# ─────────────────────────────────────────
# 3️⃣ Cadena completa (igual que el profesor)
# ─────────────────────────────────────────
chain = prompt | llm | parser

# ─────────────────────────────────────────
# 4️⃣ Endpoints Flask (expuestos para que N8N los consuma)
# ─────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'Agente PQRS activo', 'modelo': 'gemini-2.5-flash'}), 200

@app.route('/api/analizar-pqrs', methods=['POST'])
def analizar_pqrs():
    """
    N8N llama este endpoint con los datos del PQRS.
    Devuelve JSON estructurado con prioridad, departamento y mensaje al ciudadano.
    """
    try:
        import json as _json
        datos = request.get_json(force=True, silent=True)

        # Tolerar payloads envueltos/doble-codificados de n8n
        if isinstance(datos, str):
            try:
                datos = _json.loads(datos)
            except Exception:
                pass
        if isinstance(datos, dict) and len(datos) == 1:
            unica_clave = next(iter(datos))
            if isinstance(unica_clave, str) and unica_clave.strip().startswith('{'):
                try:
                    datos = _json.loads(unica_clave)
                except Exception:
                    pass
        if not isinstance(datos, dict):
            datos = {}

        tipo = datos.get('tipo') or datos.get('type')
        categoria = datos.get('categoria') or datos.get('category')
        descripcion = datos.get('descripcion') or datos.get('description')

        if not all([tipo, categoria, descripcion]):
            return jsonify({'error': f'Faltan campos. Recibido: {list(datos.keys())}'}), 400

        resultado = chain.invoke({
            "tipo": tipo,
            "categoria": categoria,
            "descripcion": descripcion,
            "format_instructions": parser.get_format_instructions()
        })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'Error en el agente'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
