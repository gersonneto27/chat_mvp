FROM python:3.11-slim

# Variáveis de ambiente padrão
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho
WORKDIR /app

RUN mkdir -p /app/static
# Instala dependências do sistema
RUN apt-get update && apt-get install -y gcc libpq-dev

# Copia o requirements e instala as dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o projeto
COPY backend/ /app/

# Expor a porta 8000
EXPOSE 8000

# Comando de entrada (definido no docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]