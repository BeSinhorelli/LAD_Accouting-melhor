#!/bin/bash

# ============================================
# LAD Accounting - Script de Execução
# ============================================

echo "========================================="
echo "   Inicializando o LAD Accounting"
echo "========================================="

# Obtém o diretório onde o script está localizado
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Diretório do projeto: $SCRIPT_DIR"

# Verifica se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Ambiente virtual não encontrado. Criando..."
    python3 -m venv venv
    echo "✅ Ambiente virtual criado."
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza o pip
echo "📌 Atualizando pip..."
pip install --upgrade pip

# Verifica e instala dependências
echo "📚 Verificando dependências..."

# Lista de pacotes necessários
PACKAGES="flask peewee dash dash-bootstrap-components plotly pandas openpyxl flask-caching python-dotenv requests"

# Instala pacotes faltantes
for package in $PACKAGES; do
    if ! pip show $package > /dev/null 2>&1; then
        echo "   Instalando $package..."
        pip install $package
    else
        echo "   ✓ $package já instalado"
    fi
done

echo "✅ Todas as dependências estão instaladas."

# Verifica se o arquivo principal existe
if [ ! -f "source/app.py" ]; then
    echo "❌ Erro: source/app.py não encontrado!"
    exit 1
fi

# Executa o programa
echo ""
echo "========================================="
echo "   Executando LAD Accounting..."
echo "========================================="
echo ""
cd source
python3 app.py