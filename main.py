import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech_v1p1beta1 as speech
from google.api_core.exceptions import GoogleAPIError

# Inicializa el cliente de Google.
try:
    speech_client = speech.SpeechClient()
    print("Clientes de Google inicializados. Conectado a la API.")
except GoogleAPIError as e:
    print(f"Error de conexión a la API de Google: {e}")
    print("Asegúrate de que las credenciales estén configuradas correctamente.")
    speech_client = None


app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Servidor de Voz en Tiempo Real en funcionamiento."}


@app.websocket("/ws/voz")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado.")

    # Cola para manejar los datos de audio
    audio_queue = asyncio.Queue()

    # Tarea para recibir datos del WebSocket
    async def receive_audio_task():
        try:
            while True:
                data = await websocket.receive_bytes()
                await audio_queue.put(data)
        except WebSocketDisconnect:
            print("Cliente desconectado.")
        except Exception as e:
            print(f"Error recibiendo datos: {e}")
        finally:
            # Pone un marcador para indicar el fin de la transmisión
            await audio_queue.put(None)

    # Tarea para enviar datos a la API de Google
    async def recognize_audio_task():
        try:
            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                    sample_rate_hertz=48000, # Aumentado para WebM/Opus
                    language_code="es-CO",
                ),
                interim_results=True
            )
            
            # Generador que pasará los datos a la API de Google
            async def generate_requests():
                while True:
                    data = await audio_queue.get()
                    if data is None:
                        break # Termina el generador
                    yield speech.StreamingRecognizeRequest(audio_content=data)

            responses = speech_client.streaming_recognize(streaming_config, generate_requests())

            async for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                
                if result.is_final:
                    print(f"Transcripción final: {transcript}")
                    await websocket.send_text(f"Recibido: {transcript}")
                else:
                    print(f"Transcripción parcial: {transcript}")

        except Exception as e:
            print(f"Error en la transmisión: {e}")
            await websocket.close()

    # Ejecuta ambas tareas concurrentemente
    await asyncio.gather(receive_audio_task(), recognize_audio_task())