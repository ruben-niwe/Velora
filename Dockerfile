FROM python:3.11-slim

WORKDIR /app

# Instalamos git y limpiamos caché
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Actualizamos pip
RUN pip install --upgrade pip

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código
COPY . .

# Hacemos ejecutable el script de inicialización
COPY init_config.sh .
RUN chmod +x init_config.sh

EXPOSE 8501

# Ejecutamos el script de inicialización
CMD ["./init_config.sh"]
