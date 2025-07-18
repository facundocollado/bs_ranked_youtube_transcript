Aquí tienes un **README.md** bien estructurado para tu repositorio `bs_ranked_youtube_transcript`, listo para subir a GitHub:

---

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
├── fetch_transcribe_rag/
│   ├── main.py             # Servicio principal (Cloud Run)
│   ├── requirements.txt    # Dependencias
│   └── Dockerfile          # Imagen de despliegue
└── shared/
    └── utils.py            # Funciones auxiliares (ID YouTube, transcripción)
```

---

## 🔧 Configuración inicial

1. **Habilitar APIs necesarias**

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
gcloud builds submit --tag gcr.io/$PROJECT_ID/fetch-transcribe-rag
gcloud run deploy bsgithub \
  --image gcr.io/$PROJECT_ID/fetch-transcribe-rag \
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
  "summary": "Resumen generado automáticamente..."
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

---

¿Quieres que además te genere un **badge de despliegue** (Cloud Run + Build Status) para agregarlo al README y quede más profesional?
