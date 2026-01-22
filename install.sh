#!/bin/bash

# Galt.ai - Universal Installer (Linux/macOS)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================="
echo "   🛡️  GALT.AI SECURITY SUITE - INSTALLER"
echo "=================================================="
echo -e "${NC}"

# Identificar OS y Binario
OS="$(uname -s)"
BINARY_NAME=""

if [ "$OS" == "Linux" ]; then
    BINARY_NAME="galt_linux"
elif [ "$OS" == "Darwin" ]; then
    BINARY_NAME="galt_mac"
fi

# ==========================================
# MODO BINARIO (Si existe el ejecutable compildado)
# ==========================================
if [ -f "./$BINARY_NAME" ]; then
    echo -e "${GREEN}[*] Binario nativo detectado: $BINARY_NAME${NC}"
    chmod +x "$BINARY_NAME"
    
    # Crear wrapper 'galt' para el binario
    echo "[*] Configurando acceso directo './galt'..."
    cat <<EOT > galt
#!/bin/bash
cd "\$(dirname "\$0")"
./$BINARY_NAME scanner "\$@"
EOT
    chmod +x galt

    # Crear wrapper 'galt-sentinel' para el binario
    echo "[*] Configurando servicio './galt-sentinel'..."
    cat <<EOT > galt-sentinel
#!/bin/bash
cd "\$(dirname "\$0")"
./$BINARY_NAME
EOT
    chmod +x galt-sentinel

    echo -e "\n${GREEN}✅ ¡INSTALACIÓN COMPLETADA (Modo Binario)!${NC}"
    echo "   👉 Escaneo manual: ./galt"
    echo "   👉 Modo vigilancia: ./galt-sentinel"
    exit 0
fi

# ==========================================
# MODO SOURCE (Python Venv)
# ==========================================
echo "[*] Verificando entorno Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[X] Python 3 no encontrado. Por favor instálalo.${NC}"
    exit 1
fi

echo "[*] Creando entorno virtual seguro (venv)..."
python3 -m venv venv
source venv/bin/activate

echo "[*] Instalando sensores y librerías..."
pip install -r requirements.txt --upgrade > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK] Dependencias instaladas.${NC}"
else
    echo -e "${RED}[X] Error instalando dependencias. Revisa requirements.txt${NC}"
    exit 1
fi

if [ ! -f .env ]; then
    echo -e "\n${BLUE}[CONFIGURACIÓN]${NC} Galt.ai requiere una API Key de Google Gemini."
    echo "Si no tienes una, obtenla gratis en: https://aistudio.google.com/"
    echo -e "${GREEN}[?] Por favor, pega tu Google API Key aquí:${NC}"
    read -p "Key: " api_key
    
    if [ -z "$api_key" ]; then
        echo "Saltando configuración de Key."
    else
        echo "GOOGLE_API_KEY=$api_key" > .env
        echo "SCAN_INTERVAL_SECONDS=3600" >> .env
        echo "LOG_LEVEL=INFO" >> .env
        echo "GALT_CLIENT_ID=${OS}_USER_$(date +%s)" >> .env
        echo -e "${GREEN}[OK] Configuración guardada en .env${NC}"
    fi
fi

echo "[*] Creando comando de acceso directo './galt'..."
cat <<EOT > galt
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
python3 runner.py "\$@"
EOT
chmod +x galt

echo "[*] Creando comando de monitoreo './galt-sentinel'..."
cat <<EOT > galt-sentinel
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
python3 sentinel.py
EOT
chmod +x galt-sentinel

echo -e "\n${GREEN}✅ ¡INSTALACIÓN COMPLETADA!${NC}"
echo "   👉 Escaneo manual: ./galt"
echo "   👉 Modo vigilancia: ./galt-sentinel"