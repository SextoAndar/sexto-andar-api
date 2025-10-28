# app/auth/__init__.py
"""
Módulo de autenticação - delegado 100% para sexto-andar-auth.

Este módulo é mantido apenas por consistência organizacional.
Toda lógica de autenticação (JWT, senhas, tokens, accounts) é gerenciada 
pelo serviço remoto sexto-andar-auth.

Endpoints de autenticação:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- POST /api/v1/auth/introspect (para validação de tokens)

Use AUTH_SERVICE_URL para se comunicar com o serviço.
"""
