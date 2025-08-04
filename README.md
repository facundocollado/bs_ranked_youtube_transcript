# 📺 Brawl Stars Ranked YouTube Transcript → Vertex AI RAG

Este proyecto permite **ingerir un video de YouTube**, **transcribirlo**, **procesarlo con un LLM (Gemini)** para generar un resumen, y finalmente **indexarlo en un RAG de Vertex AI** para que pueda ser consultado más adelante.

Se despliega automáticamente en **Cloud Run** gracias a la integración con **GitHub + Cloud Build trigger**.

---

## 🚀 Flujo del servicio

1. Envías una URL de YouTube al endpoint `/process`.
2. El servicio:

   * Extrae el **video\_id**.
   * Obtiene la **transcripción completa** usando `youtube_transcript_api`.
   * Resume el texto con **Gemini** (Vertex AI Generative Model).
   * Guarda el texto transcrito como archivo temporal.
   * Lo **indexa en un corpus de Vertex AI RAG Engine**.
3. Devuelve un JSON con `video_id` y el **resumen generado**.

---

## 🛠️ Stack Tecnológico

* **Python 3.10**
* **Flask** para el endpoint HTTP
* **youtube-transcript-api** para obtener subtítulos
* **Vertex AI (RAG Engine + Gemini LLM)**
* **Cloud Run** para ejecutar el servicio
* **Cloud Build Trigger** para CI/CD
* **Dockerfile** para empaquetar la app

---

## 📂 Estructura del repositorio

```
.
├── main.py             # Servicio Flask principal
├── process_video.py    # Clase ProcessVideo con toda la lógica
├── utils.py            # Funciones auxiliares (ID YouTube, transcripción)
├── test.py             # Script para test local sin levantar Flask
├── requirements.txt    # Dependencias
├── .env                # Variables de entorno (ignorado en git)
├── .env.example        # Plantilla para variables de entorno
└── README.md
```

---

## 🔧 Configuración inicial

1. **Habilitar APIs necesarias** en tu proyecto de GCP:

   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
   ```

2. **Configurar proyecto y variables**

   ```bash
   export PROJECT_ID=<tu-project-id>
   gcloud config set project $PROJECT_ID
   ```

3. **Configurar Cloud Build Trigger**

   * El repositorio `http://github.com/facundocollado/bs_ranked_youtube_transcript` ya está conectado.
   * Cada push a la rama principal desencadena build + deploy automático a Cloud Run.

---

## ▶️ Despliegue manual (opcional)

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/bs-ranked-youtube
gcloud run deploy bsgithub \
  --image gcr.io/$PROJECT_ID/bs-ranked-youtube \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID
```

---

## ✅ Uso del servicio

Enviar un video para procesar:

```bash
curl -X POST https://bsgithub-<REGION>-a.run.app/process \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}'
```

Respuesta esperada:

```json
{
  "video_id": "VIDEO_ID",
  "summary": "Resumen generado automáticamente...",
  "segments_count": 153
}
```

---

## 📦 Dependencias

En `requirements.txt`:

```
flask
youtube-transcript-api
google-cloud-aiplatform
vertexai
python-dotenv
```

---

## 🖥️ Desarrollo local

### 1. Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
.\venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia `.env.example` a `.env` y edita los valores:

```bash
cp .env.example .env
```

Ejemplo de `.env`:

```env
PROJECT_ID=tu-proyecto-gcp
VERTEX_REGION=us-central1
USE_VERTEX=false
```

---

### ▶️ Probar localmente

#### 1. Modo simple (sin Vertex AI)

Primero puedes probar solo la extracción de transcripción sin gastar créditos.

```bash
python test.py
```

O levantar Flask y probar:

```bash
python main.py
```

Luego envía una petición:

```bash
curl -X POST http://127.0.0.1:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=cguPzovGfMs"}'
```

---

#### 2. Activar resumen con Vertex AI

Para usar Gemini y RAG Engine (esto sí consume recursos en GCP):

```bash
# Edita .env
USE_VERTEX=true
python test.py
```

o bien:

```bash
python main.py
```

---

### 🐳 Probar con Docker localmente

```bash
docker build -t bs-local .
docker run -p 8080:8080 --env-file .env bs-local
```

Y prueba el endpoint igual:

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## 🔮 Próximos pasos

* **Agregar metadatos y timestamps** para mejorar la búsqueda en RAG.
* **Integrar Pub/Sub + Cloud Scheduler** para procesar automáticamente los últimos videos de canales específicos.
* **Añadir RAGAS** para evaluar la calidad de los resúmenes y el contexto indexado.
* Construir un **endpoint de consulta** que use Retrieval-Augmented Generation desde el corpus creado.

---

## 📝 Licencia

MIT License.

---

## 👤 Autor

**Facundo Collado**
