#!/bin/bash
set -e

echo -e "Verificando e instalando dependencias..."

# Actualizamos pip
pip install --upgrade pip

# Instalamos las dependencias desde requirements.txt
pip install --no-cache-dir -r requirements.txt

# Ejecutamos los tests antes de iniciar la aplicación
echo -e "Ejecutando batería de tests..."

pytest -v --disable-warnings

if [ $? -eq 0 ]; then
    echo -e "Tests superados exitosamente."
else
    echo -e "Los tests fallaron. Abortando inicio de la aplicación."
    exit 1
fi


echo -e "Iniciando aplicación Streamlit..."

# Iniciamos la aplicación Streamlit
python -m streamlit run src/ui/app.py --server.port 8501 