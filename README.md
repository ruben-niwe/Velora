# Velora

## Requisitos para correr la aplicación

1. **Tener instalado Docker** en tu equipo.

2. **Clonar el repositorio:**
   Abre un terminal y ejecuta:
   ```bash
   git clone [https://github.com/ruben-niwe/Velora.git](https://github.com/ruben-niwe/Velora.git)
   cd Velora

3. **Configurar las variables de entorno**
    A la misma altura del archivo `main.py` crear un archivo `.env` con la siguiente informacion: 
    `OPENAI_API_KEY = "sk-proj-..."`
    `GOOGLE_API_KEY = "AI..."`

4. **Configurar init_config.sh**
    Es importante que el init_config.sh tenga configuración LF para poder cargar, si tiene configuración CRLF cambiar a LF. 

5. **Arrancar la aplicacion**
    En el terminal, ejecuta el siguiente comando `docker-compose up`

6. **Usar la aplicacion**
    Para usar la aplicacion abre un navegador con la siguiente URL: `http://localhost:8501/`