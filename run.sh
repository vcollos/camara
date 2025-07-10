#!/bin/bash

# Definir caminhos absolutos
PROJECT_DIR="/home/collos/infraestrutura_collos/projetos/camara"
VENV_DIR="$PROJECT_DIR/.venv"

# Verificar se o diretório do projeto existe
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Erro: Diretório do projeto não encontrado: $PROJECT_DIR"
    exit 1
fi

# Verificar se o ambiente virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Erro: Ambiente virtual não encontrado: $VENV_DIR"
    exit 1
fi

# Mudar para o diretório do projeto
cd "$PROJECT_DIR"

# Ativar o ambiente virtual
source "$VENV_DIR/bin/activate"

# Verificar se o arquivo app.py existe
if [ ! -f "app.py" ]; then
    echo "Erro: Arquivo app.py não encontrado"
    exit 1
fi

# Executar o aplicativo Streamlit
echo "Iniciando aplicativo Streamlit..."
streamlit run app.py --server.port 8502 --server.address 0.0.0.0