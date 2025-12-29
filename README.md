# Velora

## Requisitos para correr la aplicación

1. **Tener instalado Docker** en tu equipo.

2. **Clonar el repositorio:**
   Abre un terminal y ejecuta:
   ```bash
   git clone [https://github.com/ruben-niwe/Velora.git](https://github.com/ruben-niwe/Velora.git)
   cd Velora

3. **Configurar las variables de entorno**
    A la misma altura del archivo `main.py` crear un archivo `.env` con la siguiente informacion: `OPENAI_API_KEY = "sk-proj-..."`

4. **Arrancar la aplicacion**
    En el terminal, ejecuta el siguiente comando `docker-compose up`

5. **Usar la aplicacion**
    Para usar la aplicacion abre un navegador con la siguiente URL: `http://localhost:8501/`