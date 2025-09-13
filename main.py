import express from "express";
import { createServer } from "http";
import { WebSocketServer, WebSocket } from "ws";
import path from "path";
import dotenv from "dotenv";
import { SpeechClient } from "@google-cloud/speech";
import { TextToSpeechClient } from "@google-cloud/text-to-speech";
import { VertexAI } from "@google-cloud/vertexai";

// Configuración de variables de entorno
dotenv.config();

/** CONFIGURACIÓN PRINCIPAL*/
const PORT = Number(process.env.PORT || 3000);
const PROJECT_ID = process.env.GOOGLE_CLOUD_PROJECT || "prj-botlabs-dev";
const LOCATION = process.env.GOOGLE_CLOUD_LOCATION || "us-central1";
const VERTEX_MODEL = process.env.VERTEX_MODEL || "gemini-1.5-flash";
const MAX_CONVERSATION_HISTORY = 6; // Límite de historial de conversación

/** SERVIDOR WEB Y WEBSOCKET */
const app = express();
const server = createServer(app);
app.use(express.static(path.join(process.cwd(), "public")));

const wss = new WebSocketServer({ server });

/** CLIENTES DE GOOGLE CLOUD */
const speechClient = new SpeechClient(); // Speech-to-Text
const ttsClient = new TextToSpeechClient(); // Text-to-Speech
const vertex = new VertexAI({ project: PROJECT_ID, location: LOCATION });

// Configuración del modelo generativo de Vertex AI
const generativeModel = vertex.getGenerativeModel({ 
  model: VERTEX_MODEL,
  generationConfig: {
    maxOutputTokens: 1024, // Límite de tokens por respuesta
    temperature: 0.7, // Creatividad de las respuestas (0-1)
    topP: 0.8, // Diversidad de respuestas (0-1)
  }
});

interface ClientState {
  recognizeStream: any;
  conversationHistory: Array<{role: string, parts: [{text: string}]}>;
  isProcessing: boolean;
  clientId: string;
}

// Mapa para almacenar el estado de todos los clientes conectados
const clientStates = new Map<WebSocket, ClientState>();

// Función para generar IDs únicos de clientes
const generateClientId = (): string => {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
};

// Función para detectar productos de Allianz mal pronunciados
function detectAllianzProduct(transcription: string): { detected: boolean, possibleProducts: string[] } {
  const allianzProducts = [
    'seguro de auto', 'seguro de vida', 'seguro de hogar', 'seguro de salud',
    'seguro empresarial', 'seguro de accidentes', 'seguro de viaje',
    'inversiones', 'ahorro', 'pensión', 'protección financiera',
    'allianz assistance', 'allianz care', 'allianz global assistance, assistencia',
    'allianz seguros', 'allianz colombia', 'allianz inversiones',
    'allianz ahorro', 'allianz pensión', 'allianz protección financiera, allianz proteccion financiera',
    'allianz seguro de auto', 'allianz seguro de vida', 'allianz seguro de hogar',
    'allianz seguro de salud', 'allianz seguro empresarial', 'allianz seguro de accidentes',
    'allianz seguro de viaje, alianza'
  ];
  
  const transcriptionLower = transcription.toLowerCase();
  const possibleMatches: string[] = [];
  
  // Búsqueda directa
  allianzProducts.forEach(product => {
    if (transcriptionLower.includes(product)) {
      possibleMatches.push(product);
    }
  });
  
  // Búsqueda por similitud si no hay coincidencias directas
  if (possibleMatches.length === 0) {
    allianzProducts.forEach(product => {
      if (calculateSimilarity(transcriptionLower, product) > 0.6) {
        possibleMatches.push(product);
      }
    });
  }
  
  return {
    detected: possibleMatches.length > 0,
    possibleProducts: possibleMatches
  };
}

// Función de similitud de strings mejorada
function calculateSimilarity(str1: string, str2: string): number {
  // Implementación simplificada para comparación de strings
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;
  
  if (longer.length === 0) return 1.0;
  
  // Contar coincidencias de caracteres
  let matches = 0;
  for (let i = 0; i < shorter.length; i++) {
    if (longer.includes(shorter[i])) matches++;
  }
  
  return matches / parseFloat(longer.length.toString());
}

// Evento para nuevas conexiones WebSocket
wss.on("connection", (ws: WebSocket) => {
  const clientId = generateClientId();
  console.log(`🔌 Cliente ${clientId} conectado.`);
  
  // Estado inicial del cliente
  clientStates.set(ws, {
    recognizeStream: null,
    conversationHistory: [],
    isProcessing: false,
    clientId
  });

  // Notificar al cliente que está conectado
  ws.send(JSON.stringify({ event: 'connected', clientId }));

  // Manejo de mensajes entrantes
  ws.on("message", async (message: Buffer) => {
    const clientState = clientStates.get(ws);
    if (!clientState) return;
    
    // Mensajes de control (Json)
    if (message.length < 100 && message.toString().startsWith('{')) {
      try {
        const msg = JSON.parse(message.toString());
        
        if (msg.event === 'start_recording') {
          console.log(`>> Cliente ${clientId}: Iniciando STT Stream.`);
          
          // Limpiar stream anterior si existe
          if (clientState.recognizeStream) {
            clientState.recognizeStream.destroy();
          }

          // Configurar y iniciar stream de reconocimiento de voz STT
          clientState.recognizeStream = speechClient.streamingRecognize({
            config: {
              encoding: 'WEBM_OPUS' as const,
              sampleRateHertz: 48000,
              languageCode: 'es-CO',
              model: 'latest_short',
              useEnhanced: true,
              profanityFilter: false,
              enableAutomaticPunctuation: true,
              audioChannelCount: 1,
            },
            interimResults: true,
            singleUtterance: false,
          })
          .on('data', (data: any) => {
            console.log(`>> Cliente ${clientId}: Datos recibidos de STT:`, 
              data.results && data.results[0] ? 'Tiene resultados' : 'Sin resultados');
            
            if (data.results && data.results[0] && data.results[0].alternatives[0]) {
              const isFinal = data.results[0].isFinal;
              const transcription = data.results[0].alternatives[0].transcript;
              
              // Solo procesar transcripciones con contenido real
              if (transcription.trim().length > 2) {
                if (isFinal) {
                  console.log(`>> Cliente ${clientId}: Transcripción final - "${transcription}"`);
                  // No enviamos la transcripción al cliente, solo la procesamos
                  processTranscription(ws, clientId, transcription);
                }
                // No enviamos transcripciones intermedias al cliente
              }
            }
          })
          .on('error', (err: any) => {
            console.error(`❌ Error en STT (cliente ${clientId}):`, err);
            ws.send(JSON.stringify({ 
              event: 'error', 
              message: 'Error en reconocimiento de voz',
              code: 'STT_ERROR'
            }));
            clientState.recognizeStream = null;
          })
          .on('end', () => {
            console.log(`>> Cliente ${clientId}: Stream de STT finalizado.`);
            clientState.recognizeStream = null;
          });

        } else if (msg.event === 'stop_recording') {
          console.log(`>> Cliente ${clientId}: Deteniendo STT Stream.`);
          if (clientState.recognizeStream) {
            clientState.recognizeStream.end();
            clientState.recognizeStream = null;
          }
          ws.send(JSON.stringify({ event: 'recording_stopped' }));
        } else if (msg.event === 'clear_history') {
          console.log(`>> Cliente ${clientId}: Limpiando historial.`);
          clientState.conversationHistory = [];
          ws.send(JSON.stringify({ event: 'history_cleared' }));
        } else if (msg.event === 'ping') {
          ws.send(JSON.stringify({ event: 'pong', timestamp: new Date().toISOString() }));
        }
      } catch (e) {
        console.error(`❌ Error procesando mensaje JSON (cliente ${clientId}):`, e);
      }
    } 
    else if (clientState.recognizeStream) {
      try {
        clientState.recognizeStream.write(message);
      } catch (e) {
        console.error(`❌ Error escribiendo en STT (cliente ${clientId}):`, e);
      }
    }
  });

  const processTranscription = async (ws: WebSocket, clientId: string, transcription: string) => {
    const clientState = clientStates.get(ws);
    if (!clientState || clientState.isProcessing) return;
    
    clientState.isProcessing = true;
    
    try {
      // Agregar al historial de conversación
      clientState.conversationHistory.push({
        role: 'user',
        parts: [{text: transcription}]
      });
      
      // Limitar historial para evitar sobrecargas
      if (clientState.conversationHistory.length > MAX_CONVERSATION_HISTORY) {
        clientState.conversationHistory = clientState.conversationHistory.slice(-MAX_CONVERSATION_HISTORY);
      }
      
      // Notificar al cliente que se está procesando
      ws.send(JSON.stringify({ 
        event: 'processing_started',
        timestamp: new Date().toISOString()
      }));
      
      // Detectar posibles productos de Allianz
      const productDetection = detectAllianzProduct(transcription);
      
      // Preparar el mensaje con instrucciones especializadas en Allianz
      let systemMessage = `Eres "Alli", un asistente de voz especializado en Allianz Colombia. 
      Responde de manera natural, amable y conversacional sobre seguros, inversiones y servicios financieros de Allianz.
      
      Información clave sobre Allianz Colombia:
      - Allianz es una de las aseguradoras más grandes y confiables del mundo
      - Ofrece seguros de auto, vida, hogar, salud, empresariales, accidentes y viaje
      - Tiene productos de inversión, ahorro y protección financiera
      - Operan en Colombia desde 1997
      - Tienen sedes en Bogotá, Medellín, Cali, Barranquilla y otras ciudades principales
      - Allianz ofrece soluciones digitales para la gestión de seguros
      - Tienen programas de fidelización y beneficios para clientes
      
      Responde siempre de manera útil y precisa sobre productos Allianz.
      Si el usuario pregunta sobre algo no relacionado, amablemente redirige la conversación
      hacia los productos y servicios de Allianz, destacando sus beneficios.
      
      Mantén un tono amable, profesional y servicial. Sé conciso pero proporciona información valiosa.`;
      
      if (productDetection.detected) {
        systemMessage += `\n\nEl usuario parece estar preguntando sobre productos de Allianz. 
        Posibles productos detectados: ${productDetection.possibleProducts.join(', ')}. 
        Proporciona información útil sobre estos productos específicos.`;
      }
      
      // Crear el contenido con instrucciones del sistema
      const contents = [
        {
          role: "user",
          parts: [{
            text: systemMessage + "\n\nPregunta del usuario: " + transcription
          }]
        }
      ];
      
      // Generar respuesta con Vertex AI
      const result = await generativeModel.generateContent({
        contents: contents,
      });
      
      const responseText = result.response.candidates?.[0]?.content?.parts?.[0]?.text;
      
      if (responseText) {
        console.log(`>> Cliente ${clientId}: Respuesta - "${responseText}"`);
        
        // Sintetizar voz a partir de la respuesta
        const [ttsResponse] = await ttsClient.synthesizeSpeech({
          input: { text: responseText },
          voice: { 
            languageCode: 'es-ES', 
            ssmlGender: 'FEMALE' as const,
            name: 'es-ES-Standard-A'
          },
          audioConfig: { 
            audioEncoding: 'MP3' as const,
            speakingRate: 1.0,
            pitch: 0.0
          },
        });
        
        if (ttsResponse.audioContent) {
          // Enviar audio al cliente
          ws.send(JSON.stringify({ 
            event: 'audio_start',
            timestamp: new Date().toISOString()
          }));
          
          const audioBase64 = ttsResponse.audioContent.toString('base64');
          ws.send(JSON.stringify({
            event: 'audio_data',
            data: audioBase64,
            format: 'mp3'
          }));
          
          ws.send(JSON.stringify({ 
            event: 'audio_end',
            timestamp: new Date().toISOString()
          }));
        }
      }
    } catch (e: any) {
      // Manejo de errores en el procesamiento
      console.error(`❌ Error procesando transcripción (cliente ${clientId}):`, e);
      ws.send(JSON.stringify({ 
        event: 'error', 
        message: 'Error procesando solicitud',
        code: 'PROCESSING_ERROR'
      }));
    } finally {
      // Finalizar procesamiento
      clientState.isProcessing = false;
      ws.send(JSON.stringify({ 
        event: 'processing_completed',
        timestamp: new Date().toISOString()
      }));
    }
  };

  // Manejo de desconexiones
  ws.on("close", () => {
    console.log(`>> Cliente ${clientId} desconectado.`);
    const clientState = clientStates.get(ws);
    if (clientState && clientState.recognizeStream) {
      clientState.recognizeStream.destroy();
    }
    clientStates.delete(ws);
  });

  // Manejo de errores en la conexión WebSocket
  ws.on('error', (error) => {
    console.error(`❌ Error WS (cliente ${clientId}):`, error);
    const clientState = clientStates.get(ws);
    if (clientState && clientState.recognizeStream) {
      clientState.recognizeStream.destroy();
    }
    clientStates.delete(ws);
  });
});

// Endpoint de salud para monitoreo
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'OK', 
    clients: clientStates.size,
    timestamp: new Date().toISOString()
  });
});

// Iniciar el servidor
server.listen(PORT, () => {
  console.log(`✅ Servidor Allianz escuchando en http://localhost:${PORT}`);
});
