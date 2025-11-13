# Endpoint Necessário no Serviço de Autenticação

## Contexto

A API de imóveis (sexto-andar-api) precisa que o serviço de autenticação (sexto-andar-auth) forneça um endpoint para buscar informações de usuários por ID. Isso é necessário para implementar completamente a **US21**, onde proprietários visualizam detalhes dos usuários que agendaram visitas em seus imóveis.

## Endpoint Requerido

### `GET /auth/admin/users/{user_id}`

Busca informações detalhadas de um usuário específico por ID.

---

## Especificação Completa

### Request

**Method**: `GET`

**Path**: `/auth/admin/users/{user_id}`

**Path Parameters**:
- `user_id` (UUID, required): ID único do usuário a ser consultado

**Authentication**: Required (JWT Bearer Token)
- Token deve ser de um usuário com role `PROPERTY_OWNER` ou `ADMIN`
- Proprietários podem buscar informações de usuários que agendaram visitas em suas propriedades
- Admins podem buscar informações de qualquer usuário

**Headers**:
```
Authorization: Bearer {jwt_token}
```

Ou usando cookies (como no resto da aplicação):
```
Cookie: access_token={jwt_token}
```

---

### Response Success (200 OK)

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johndoe",
  "fullName": "John Doe",
  "email": "john.doe@example.com",
  "phoneNumber": "+5511999999999",
  "role": "USER",
  "createdAt": "2025-01-15T10:30:00Z",
  "isActive": true
}
```

**Response Schema**:
```python
{
  "id": str (UUID),          # ID único do usuário
  "username": str,            # Nome de usuário
  "fullName": str,            # Nome completo
  "email": str,               # Email
  "phoneNumber": str | null,  # Telefone (opcional)
  "role": str,                # USER | PROPERTY_OWNER | ADMIN
  "createdAt": str (ISO8601), # Data de criação da conta
  "isActive": bool            # Se a conta está ativa
}
```

---

### Response Errors

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

**Quando**: Token JWT ausente ou inválido

---

#### 403 Forbidden
```json
{
  "detail": "Insufficient permissions to access user information"
}
```

**Quando**: Usuário autenticado não tem permissão para acessar informações de usuários
- Usuários regulares (role USER) não podem acessar este endpoint
- Apenas PROPERTY_OWNER e ADMIN

---

#### 404 Not Found
```json
{
  "detail": "User not found"
}
```

**Quando**: Usuário com o ID fornecido não existe no banco de dados

---

## Regras de Negócio

### Controle de Acesso

1. **ADMIN**:
   - Pode buscar informações de qualquer usuário
   - Sem restrições

2. **PROPERTY_OWNER**:
   - Pode buscar informações APENAS de usuários que:
     - Agendaram visitas em suas propriedades OU
     - Fizeram propostas em suas propriedades OU
     - É ele próprio (seu próprio ID)
   - **⚠️ SEGURANÇA CRÍTICA**: DEVE validar com a API de imóveis antes de retornar os dados
   - **NÃO** pode buscar informações de usuários aleatórios da plataforma

3. **USER**:
   - Não tem acesso ao endpoint
   - Retornar 403 Forbidden

### 🔒 Validação de Segurança Obrigatória

Para PROPERTY_OWNER, o serviço de auth **DEVE** fazer uma chamada ao endpoint interno da API de imóveis para validar se existe relação entre o usuário solicitado e o proprietário:

```
GET {PROPERTIES_API_URL}/api/internal/check-user-property-relation?user_id={user_id}&owner_id={owner_id}
Header: X-Internal-Secret: {shared_secret}

Response:
{
  "has_relation": true/false,
  "has_visit": true/false,
  "has_proposal": true/false
}
```

Se `has_relation = false`, retornar **403 Forbidden**.

### Privacidade e Segurança

- ❌ **Não** retornar senha (hash ou texto puro)
- ❌ **Não** retornar tokens de autenticação
- ✅ Retornar apenas informações básicas de perfil
- ✅ Log de acesso para auditoria (quem buscou informações de quem)

---

## Implementação Sugerida (FastAPI)

### Controller/Router

```python
# app/controllers/admin_controller.py ou app/controllers/user_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.services.user_service import UserService
from app.dtos.user_dto import UserInfoResponse
from app.auth.dependencies import get_current_user, require_role, AuthUser
from app.models.account import RoleEnum

router = APIRouter(tags=["admin"])


@router.get(
    "/admin/users/{user_id}",
    response_model=UserInfoResponse,
    summary="Get User Information by ID (Admin/Property Owner)"
)
async def get_user_by_id(
    user_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific user.
    
    **Authentication required:** PROPERTY_OWNER or ADMIN role
    
    **Access Control:**
    - Admins can access any user information
    - Property owners can ONLY access information of users who:
      - Have visits scheduled at their properties
      - Have made proposals for their properties
      - Are themselves (own user_id)
    
    **Returns:** User profile information (excluding sensitive data like passwords)
    
    **Error responses:**
    - `401 Unauthorized`: Not authenticated
    - `403 Forbidden`: Insufficient permissions or no relation with user
    - `404 Not Found`: User does not exist
    """
    # Check if user has required role
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.PROPERTY_OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access user information"
        )
    
    # SECURITY: Property owners must have relation with the user
    if current_user.role == RoleEnum.PROPERTY_OWNER:
        # Allow access to own information
        if user_id != current_user.id:
            # Validate relation with properties API
            has_relation = await check_user_property_relation(
                user_id=user_id,
                owner_id=current_user.id
            )
            
            if not has_relation:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access information of users who interacted with your properties"
                )
    
    # Get user information
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Optional - Log access for audit trail
    # audit_service.log_user_info_access(
    #     accessed_by=current_user.id,
    #     accessed_user=user_id
    # )
    
    return UserInfoResponse.from_account(user)
```

---

### Helper Function - Validação de Relação

```python
# app/services/property_relation_service.py ou no controller

import httpx
from uuid import UUID
from app.settings import settings
import logging

logger = logging.getLogger(__name__)


async def check_user_property_relation(user_id: UUID, owner_id: UUID) -> bool:
    """
    Verifica se o usuário tem relação (visita/proposta) com propriedades do owner.
    
    Faz chamada ao endpoint interno da API de imóveis.
    
    Args:
        user_id: ID do usuário a ser verificado
        owner_id: ID do proprietário
    
    Returns:
        True se existe relação, False caso contrário
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.PROPERTIES_API_URL}/api/internal/check-user-property-relation",
                params={
                    "user_id": str(user_id),
                    "owner_id": str(owner_id)
                },
                headers={
                    "X-Internal-Secret": settings.INTERNAL_API_SECRET
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("has_relation", False)
            elif response.status_code == 401:
                logger.error("Invalid internal API secret")
                return False
            else:
                logger.error(f"Properties API returned status {response.status_code}")
                return False
    
    except httpx.TimeoutException:
        logger.error("Timeout connecting to properties API")
        return False
    except httpx.RequestError as e:
        logger.error(f"Error connecting to properties API: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking user-property relation: {e}")
        return False
```

### Variáveis de Ambiente Necessárias

Adicionar no `.env` do **sexto-andar-auth**:

```bash
# URL da API de imóveis (comunicação interna via Docker network)
PROPERTIES_API_URL=http://sexto-andar-properties-api:8000

# Secret compartilhado para autenticação entre serviços
# IMPORTANTE: Deve ser EXATAMENTE o mesmo valor nos dois serviços (auth e properties)
INTERNAL_API_SECRET=change-this-to-secure-random-secret-in-production

# JWT Settings (já devem existir, garantir que são estes valores)
JWT_SECRET_KEY=P2M3wtplsZOfysdRFaS9Q2sdi0JAkWY1IstrT4-seqY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ IMPORTANTE - Secrets Compartilhados:**

Os seguintes valores **DEVEM** ser idênticos nos dois serviços:

1. **INTERNAL_API_SECRET**: 
   - Usado para autenticar chamadas entre serviços
   - No sexto-andar-api está: `change-this-to-secure-random-secret-in-production`
   - **Copiar este exato valor** ou gerar um novo e atualizar nos dois serviços

2. **JWT_SECRET_KEY**:
   - Já configurado: `P2M3wtplsZOfysdRFaS9Q2sdi0JAkWY1IstrT4-seqY`
   - Manter este valor (já é o mesmo nos dois serviços)

---

### DTO/Schema

```python
# app/dtos/user_dto.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional


class UserInfoResponse(BaseModel):
    """Response model for user information"""
    id: UUID
    username: str
    fullName: str
    email: EmailStr
    phoneNumber: Optional[str] = None
    role: str  # "USER" | "PROPERTY_OWNER" | "ADMIN"
    createdAt: datetime
    isActive: bool = True
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "fullName": "John Doe",
                "email": "john.doe@example.com",
                "phoneNumber": "+5511999999999",
                "role": "USER",
                "createdAt": "2025-01-15T10:30:00Z",
                "isActive": True
            }
        }
    
    @classmethod
    def from_account(cls, account):
        """Create response from Account model"""
        return cls(
            id=account.id,
            username=account.username,
            fullName=account.fullName,
            email=account.email,
            phoneNumber=account.phoneNumber,
            role=account.role.value if hasattr(account.role, 'value') else account.role,
            createdAt=account.created_at,
            isActive=account.is_active if hasattr(account, 'is_active') else True
        )
```

---

### Service Layer

```python
# app/services/user_service.py

from sqlalchemy.orm import Session
from app.models.account import Account
from uuid import UUID
from typing import Optional


class UserService:
    """Service for User operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: UUID) -> Optional[Account]:
        """Get user by ID"""
        return self.db.query(Account)\
            .filter(Account.id == user_id)\
            .first()
```

---

### Registrar o Router

```python
# app/main.py

from app.controllers.admin_controller import router as admin_router

# ...

app.include_router(admin_router, prefix="/auth")

# Ou se já existir um auth_router:
# auth_router.include_router(admin_router)
```

---

## Exemplo de Uso

### Request usando cURL

```bash
# Login como property owner
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "password": "senha123"}' \
  -c cookies.txt

# Buscar informações de um usuário
curl -X GET http://localhost:8001/auth/admin/users/123e4567-e89b-12d3-a456-426614174000 \
  -b cookies.txt
```

### Request usando Python

```python
import requests

# Login
login_response = requests.post(
    "http://localhost:8001/auth/login",
    json={"username": "johndoe", "password": "senha123"}
)
cookies = login_response.cookies

# Buscar informações do usuário
user_response = requests.get(
    "http://localhost:8001/auth/admin/users/123e4567-e89b-12d3-a456-426614174000",
    cookies=cookies
)

if user_response.status_code == 200:
    user_data = user_response.json()
    print(f"Nome: {user_data['fullName']}")
    print(f"Email: {user_data['email']}")
    print(f"Telefone: {user_data['phoneNumber']}")
```

---

## Testes

### Casos de Teste Obrigatórios

1. **✅ Admin pode buscar qualquer usuário**
   - Login como admin
   - GET /auth/admin/users/{any_user_id}
   - Esperado: 200 OK com dados do usuário

2. **✅ Property owner pode buscar seu próprio ID**
   - Login como property owner
   - GET /auth/admin/users/{own_user_id}
   - Esperado: 200 OK com dados do usuário

3. **✅ Property owner pode buscar usuário com relação (visitante)**
   - Login como property owner
   - User X tem visita agendada em propriedade do owner
   - GET /auth/admin/users/{user_x_id}
   - Mock: Properties API retorna has_relation=true
   - Esperado: 200 OK com dados do usuário

4. **❌ Property owner NÃO pode buscar usuário sem relação**
   - Login como property owner
   - User Y nunca interagiu com propriedades do owner
   - GET /auth/admin/users/{user_y_id}
   - Mock: Properties API retorna has_relation=false
   - Esperado: 403 Forbidden

5. **❌ Usuário regular não pode acessar**
   - Login como user regular
   - GET /auth/admin/users/{any_user_id}
   - Esperado: 403 Forbidden

6. **❌ Sem autenticação**
   - GET /auth/admin/users/{any_user_id} (sem token)
   - Esperado: 401 Unauthorized

7. **❌ Usuário não existe**
   - Login como admin
   - GET /auth/admin/users/{invalid_uuid}
   - Esperado: 404 Not Found

8. **✅ Resposta não contém senha**
   - Login como admin
   - GET /auth/admin/users/{user_id}
   - Verificar que response não contém campos 'password' ou 'hashed_password'

9. **❌ Properties API indisponível**
   - Login como property owner
   - GET /auth/admin/users/{other_user_id}
   - Mock: Properties API timeout/erro
   - Esperado: 403 Forbidden (fail-safe)

---

## Alternativa: Batch Endpoint

Para melhor performance quando a API de imóveis precisa buscar múltiplos usuários, considere também implementar:

### `POST /auth/admin/users/batch`

```json
// Request
{
  "user_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ]
}

// Response
{
  "users": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "username": "johndoe",
      "fullName": "John Doe",
      // ...
    },
    // ...
  ],
  "not_found": [
    "323e4567-e89b-12d3-a456-426614174002"
  ]
}
```

Isso permite buscar informações de múltiplos usuários em uma única requisição, reduzindo latência.

---

## Integração com sexto-andar-api

Após implementação, o código em `sexto-andar-api/app/auth/auth_client.py` precisa ser descomentado:

```python
async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Get user information from auth service"""
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.auth_service_url}/auth/admin/users/{user_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"User {user_id} not found in auth service")
                return None
            else:
                logger.error(f"Auth service returned status {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        return None
```

---

## Checklist de Implementação

- [ ] Criar DTO `UserInfoResponse`
- [ ] Criar service method `get_user_by_id()`
- [ ] Criar endpoint `GET /auth/admin/users/{user_id}`
- [ ] Implementar controle de acesso (ADMIN e PROPERTY_OWNER apenas)
- [ ] Validar que senha não é retornada na resposta
- [ ] Adicionar tratamento de erros (401, 403, 404)
- [ ] Registrar router no main.py
- [ ] Escrever testes unitários
- [ ] Escrever testes de integração
- [ ] Testar manualmente com cURL
- [ ] Atualizar documentação da API (Swagger)
- [ ] (Opcional) Implementar batch endpoint
- [ ] (Opcional) Adicionar log de auditoria
- [ ] Notificar equipe da API de imóveis para descomentar integração

---

## Prioridade

🔴 **ALTA** - Necessário para completar US21 (Must Have)

---

## Contato

Para dúvidas sobre a integração, consultar:
- Repositório: sexto-andar-api
- Arquivo: `app/auth/auth_client.py`
- Documentação: `docs/US21_IMPLEMENTATION.md`
