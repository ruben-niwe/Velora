FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --- NUEVA LÍNEA: ACTUALIZAR PIP ---
RUN pip install --upgrade pip
# -----------------------------------

# Luego instalamos las librerías con el pip nuevo
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/ui/app.py"]