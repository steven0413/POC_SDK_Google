Asistente de Voz Allianz Colombia
<div align="center">
https://www.allianz.com/content/dam/onemarketing/azcom/Allianz_com/logo/allianz-logo.svg

Asistente de voz conversacional especializado en seguros e inversiones
Powered by Google Vertex AI & Gemini
</div>

📋 Tabla de Contenidos
Descripción del Proyecto

Características Principales

Arquitectura del Sistema

Tecnologías Utilizadas

Requisitos del Sistema

Instalación y Configuración

Variables de Entorno

Uso del Sistema

Estructura del Proyecto

Costos y Optimización

Solución de Problemas

Contribución

Licencia

🚀 Descripción del Proyecto
Asistente de voz inteligente especializado en productos y servicios de Allianz Colombia. Proporciona respuestas contextuales en tiempo real mediante una interfaz de voz conversacional, utilizando tecnologías de IA generativa de Google Cloud.

Objetivos principales:

Brindar información precisa sobre seguros e inversiones Allianz

Ofrecer una experiencia de usuario natural y conversacional

Resolver consultas comunes de clientes de manera eficiente

Operar con alta disponibilidad y escalabilidad

✨ Características Principales
🤖 Especialización Allianz: Modelo de IA entrenado específicamente para productos de seguros

🎤 Voz en Tiempo Real: Comunicación fluida voz-a-voz con latencia mínima

🔍 Detección de Intención: Reconocimiento de productos Allianz incluso con pronunciación imperfecta

💬 Contexto Conversacional: Mantiene el historial de conversación para respuestas coherentes

🎨 Interfaz Optimizada: Diseño minimalista centrado en la experiencia de voz

⚡ Alta Disponibilidad: Arquitectura preparada para múltiples usuarios concurrentes

Componentes Principales
Frontend Web: Interfaz de usuario para captura y reproducción de audio

Servidor WebSocket: Gestión de conexiones en tiempo real

Procesamiento de Audio: Transcripción y síntesis con Google Cloud

Motor de IA: Generación de respuestas contextuales con Vertex AI

Gestión de Estado: Control de conversaciones y sesiones de usuario

🛠️ Tecnologías Utilizadas
Frontend
HTML5/CSS3: Interfaz de usuario responsive

WebSocket API: Comunicación bidireccional en tiempo real

MediaRecorder API: Captura de audio desde el micrófono

JavaScript ES6+: Lógica de interacción del cliente

Backend
Node.js: Runtime de JavaScript del lado del servidor

TypeScript: Lenguaje tipado para mayor robustez

Express.js: Framework para servidor web

ws: Librería WebSocket para conexiones persistentes

Servicios Google Cloud
Speech-to-Text: Transcripción de voz a texto en tiempo real

Text-to-Speech: Síntesis de texto a voz natural

Vertex AI: Modelo Gemini para generación de respuestas

Google Cloud SDK: Integración con servicios de Google Cloud

📋 Requisitos del Sistema
Requisitos Mínimos
Node.js 16.x o superior

npm 8.x o superior

Navegador moderno con soporte para WebAudio API

Conexión a Internet para servicios Google Cloud

Requisitos Recomendados
Node.js 18.x LTS

2 GB de RAM mínimo

1 CPU núcleo

Navegador Chrome 90+ o Firefox 88+

📁 Estructura del Proyecto
text
asistente-allianz/
├── src/
│   └── server.ts              # Servidor principal
├── public/
│   ├── index.html             # Interfaz de usuario
│   ├── style.css              # Estilos principales
│   └── script.js              # Lógica del cliente
├── dist/                      # Archivos compilados (generado)
├── .env                       # Variables de entorno
├── package.json
├── tsconfig.json
└── README.md


💰 Costos y Optimización
Estimación de Costos
Servicio	Costo por 1000 interacciones
Speech-to-Text	~$6.00
Vertex AI	~$0.15
Text-to-Speech	~$0.80
Total estimado	~$6.95


🤝 Contribución
¡Las contribuciones son bienvenidas! Para contribuir:

Hacer fork del proyecto

Crear una rama para la funcionalidad (git checkout -b feature/nueva-funcionalidad)

Commit de los cambios (git commit -m 'Agrega nueva funcionalidad')

Push a la rama (git push origin feature/nueva-funcionalidad)

Abrir un Pull Request

Desarrollado con ❤️ para Allianz Colombia




































