# Velora

## Requisitos para correr la aplicación con Docker

1. **Tener instalado Docker** en tu equipo.

2. **Clonar el repositorio:**
   Abre un terminal y ejecuta:
   ```bash
   git clone https://github.com/ruben-niwe/Velora.git
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


## Requisitos para correr la aplicación sin Docker

1. Requisitos previos:
    - Tener instalado Python 3.10 o superior

2. **Clonar el repositorio:**
   Abre un terminal y ejecuta:
   ```bash
   git clone https://github.com/ruben-niwe/Velora.git
   cd Velora

### 3. Crear y activar el entorno virtual

#### En **Windows**
Abre una terminal (CMD o PowerShell) y ejecuta:

```bash
python -m venv env
.\env\Scripts\activate
```
#### En Mac o Linux
```bash
python -m venv env
source env/bin/activate
```

4. **Instalar dependencias**: Una vez activado el entorno, instala las librerias necesarias
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt

5. **Configurar las variables de entorno**
    A la misma altura del archivo `main.py` crear un archivo `.env` con la siguiente informacion: 
    `OPENAI_API_KEY = "sk-proj-..."`
    `GOOGLE_API_KEY = "AI..."`

6. **Correr la aplicacion**:
    Para arrancar la aplicacion ejecuta 
    ```bash
    python -m streamlit run src/ui/app.py

7. **Usar la aplicacion**:
    El navegador deberia de abrir automáticamente. Si no, accede a: `http://localhost:8501/`


