#!/bin/bash
cd ~/infraestrutura_collos/projetos/camara
source .venv/bin/activate
streamlit run app.py --server.port 8502 --server.address 0.0.0.0