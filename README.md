# 🎬 X (Twitter) Video Downloader Bot

Un bot de Telegram eficiente, ligero y libre de anuncios para descargar videos de X (Twitter) directamente a tu dispositivo con un solo toque desde el menú de compartir.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot_API-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-red?style=for-the-badge)

---

## 🚀 Motiva del Proyecto

Las herramientas y páginas web de terceros para descargar videos de X suelen estar saturadas de publicidad agresiva, acortadores de enlaces y pop-ups incómodos. Este proyecto nace para **resolver ese problema**, ofreciendo una solución limpia, rápida y automatizada que se integra directamente con el flujo nativo de compartir en smartphones.

---

## ✨ Características

- 📩 **Integración Nativa:** Comparte el enlace del tweet directamente desde la app de X hacia Telegram.
- 🚫 **Cero Publicidad:** Sin anuncios, acortadores ni redirecciones.
- ⚡ **Descarga Directa:** Entrega el archivo en formato `.mp4` listo para guardar en la galería del teléfono.
- 🧹 **Gestión Eficiente de Memoria:** Limpieza automática de archivos temporales en el servidor tras cada envío exitoso.
- 📡 **Despliegue 24/7:** Preparado para ejecutarse de forma continua como un *Background Worker* en plataformas Cloud (Render, Railway, Fly.io).

---

## 🛠️ Tecnologías Utilizadas

- **[Python](https://www.python.org/):** Lenguaje principal.
- **[python-telegram-bot](https://python-telegram-bot.org/):** Wrapper asíncrono para interactuar con la API de Telegram.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Motor de extracción y procesamiento de video.

---

## 📂 Estructura del Proyecto

```text
.
├── bot.py               # Lógica principal del bot y manejo de eventos
├── requirements.txt     # Dependencias de Python
├── .gitignore           # Exclusión de credenciales y carpetas temporales
└── README.md            # Documentación del proyecto

---

## ⚙️ Instalación y Configuración Local

### Prerrequisitos

* Python 3.10 o superior.
* Token de Bot obtenido mediante [@BotFather](https://t.me/BotFather) en Telegram.

### Pasos de ejecución

1. **Clonar el repositorio:**
```bash
git clone [https://github.com/TU_USUARIO/TU_REPOSOTORIO.git](https://github.com/TU_USUARIO/TU_REPOSOTORIO.git)
cd TU_REPOSOTORIO

```


2. **Crear y activar un entorno virtual (opcional pero recomendado):**

python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate


3. **Instalar dependencias:**

pip install -r requirements.txt


4. **Configurar la Variable de Entorno:**

Configura tu token de Telegram en tu entorno local o reemplázalo temporalmente para pruebas locales:
export TELEGRAM_BOT_TOKEN="tu_token_aqui"

5. **Iniciar el bot:**

python bot.py

