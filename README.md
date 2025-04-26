# Chat MVP - Teste Técnico Nível Pleno

Este projeto é um MVP de sistema de chat interno, onde todas as mensagens são moderadas automaticamente antes de chegar aos destinatários.

---

## Funcionalidades

- Autenticação JWT
- Sistema de permissões: usuário normal e admin
- Criação de salas públicas e privadas
- Envio de mensagens moderadas automaticamente
- WebSocket para mensagens em tempo real e membros online
- Moderação automática de mensagens via Celery
- API documentada com Swagger

---

## Tecnologias

- Django 5
- Django REST Framework
- Django Channels (WebSocket)
- Celery + Redis
- PostgreSQL
- Docker + Docker Compose

---

## Como rodar o projeto

**Pré-requisitos**:
- Docker
- Docker Compose

**Passos**:

1. Clone o projeto:

```bash
git clone https://github.com/seu-usuario/chat-mvp.git
cd chat-mvp

**Monte o ambiente de desenvolvimento**
docker-compose up --build

** Crie um usuário administrador**
docker compose run web python manage.py createsuperuser

** Caso queira rodar os testes**
docker compose run web python manage.py test
```