from groq import AsyncGroq
from app.core.config import settings
import json
import httpx
import tempfile
import os

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def transcribir_audio(url_audio: str) -> str:
    if not url_audio or url_audio.startswith("http://localhost") or "mock" in url_audio:
        return "El conductor indica que tiene un problema con su vehículo (transcripción simulada por falta de archivo real)."
        
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url_audio)
            response.raise_for_status()
            
            with tempfile.NamedNamedTemporaryFile(delete=False, suffix=".m4a") as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
                
            with open(tmp_file_path, "rb") as audio_file:
                transcription = await client.audio.transcriptions.create(
                    file=(os.path.basename(tmp_file_path), audio_file.read()),
                    model="whisper-large-v3",
                    response_format="json",
                )
            os.remove(tmp_file_path)
            return transcription.text
    except Exception as e:
        print(f"Error en Whisper: {e}")
        return "No se pudo transcribir el audio."

async def analizar_incidente_ia(texto_audio: str = "", url_imagen: str = ""):
    # Si texto_audio es una URL, lo transcribimos primero
    if texto_audio.startswith("http"):
        texto_transcrito = await transcribir_audio(texto_audio)
    else:
        texto_transcrito = texto_audio

    prompt = f"""
    Actúa como un experto mecánico automotriz.
    El conductor reporta el siguiente problema (transcrito de su nota de voz): '{texto_transcrito}'.
    Además, proporcionó una fotografía en esta URL: {url_imagen}
    
    Asume que la imagen muestra signos consistentes con la descripción (Ej: motor humeando, llanta pinchada).
    
    Devuelve estrictamente un JSON con la siguiente estructura:
    {{
      "proveedor": "Groq Whisper + LLaMA3",
      "resultado_analisis": "Breve explicación técnica y causa probable del problema",
      "probabilidad_falla": 95.50,
      "recomendacion": "Herramientas o repuestos sugeridos que el mecánico debe llevar"
    }}
    """
    
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente de IA que devuelve únicamente JSON válido."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-8b-8192",
        response_format={"type": "json_object"},
    )
    
    contenido = chat_completion.choices[0].message.content
    return json.loads(contenido)
