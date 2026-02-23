# Usa uma imagem leve do Python
FROM python:3.11-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# [CORREÇÃO DE FUSO HORÁRIO]
# 1. Adicionado 'tzdata' para o sistema reconhecer fusos horários
# 2. Mantido ca-certificates e outras dependências do GStreamer/Flet
RUN apt-get update && apt-get install -y \
    tzdata \
    gcc \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# [CORREÇÃO DE FUSO HORÁRIO] Define o fuso padrão para Brasília na construção
ENV TZ=America/Sao_Paulo

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto
COPY . .

# === CONFIGURAÇÃO DE REDE PADRONIZADA ===
ENV PORT=8000
ENV FLET_SERVER_PORT=8000
ENV FLET_FORCE_WEB_VIEW=true
ENV PYTHONPATH=/app

# Expõe a porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "src/main.py"]