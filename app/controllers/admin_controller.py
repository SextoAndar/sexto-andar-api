# app/controllers/admin_controller.py
"""
Controlador de Admin - VAZIO

NOTA IMPORTANTE:
- Toda a gerência de contas (usuários, senhas, papéis) é responsabilidade do serviço
  sexto-andar-auth, que gerencia o modelo Account no mesmo banco de dados PostgreSQL.
- Este arquivo está vazio porque endpoints de admin devem ser chamados diretamente
  em sexto-andar-auth, não neste repositório.
- Este serviço (sexto-andar-api) foca apenas em:
  1. Validar tokens via sexto-andar-auth (autenticação)
  2. Gerenciar domínio de propriedades (Properties, Proposals, Visits)
  
Se precisar de endpoints de administração de usuários, use:
  POST /api/v1/auth/admin/users
  GET /api/v1/auth/admin/users
  GET /api/v1/auth/admin/users/{user_id}
  PUT /api/v1/auth/admin/users/{user_id}
  DELETE /api/v1/auth/admin/users/{user_id}
  PUT /api/v1/auth/admin/users/{user_id}/password
  
Vide: https://github.com/moonshinerd/sexto-andar-auth
"""
from fastapi import APIRouter

# Prefix é definido no main.py via settings
router = APIRouter(tags=["admin"])
