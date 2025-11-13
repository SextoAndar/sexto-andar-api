# 📋 RESUMO: Implementação do Endpoint para o Auth Service

## 🎯 O que precisa ser feito no repositório `sexto-andar-auth`

Implementar endpoint seguro para que proprietários possam visualizar dados de usuários que interagiram com suas propriedades.

---

## ✅ Já está implementado no `sexto-andar-api`

### Endpoint Interno Criado
✅ `GET /api/internal/check-user-property-relation`
- Valida se um usuário tem relação (visitas/propostas) com propriedades de um owner
- Requer header `X-Internal-Secret` para autenticação inter-serviços
- Arquivo: `app/controllers/internal_controller.py`

### Configuração Adicionada
✅ `INTERNAL_API_SECRET` no `.env` e `settings.py`
- Usado para autenticar chamadas entre serviços
- **IMPORTANTE**: Deve ser o mesmo secret nos dois serviços

---

## 🔴 O que implementar no `sexto-andar-auth`

### 1. Endpoint Principal

**Path**: `GET /auth/admin/users/{user_id}`

**Controle de Acesso**:
- ✅ ADMIN: pode buscar qualquer usuário
- ⚠️ PROPERTY_OWNER: pode buscar APENAS usuários com relação
  - Próprio ID
  - Usuários que agendaram visitas em suas propriedades  
  - Usuários que fizeram propostas em suas propriedades
- ❌ USER: sem acesso (403 Forbidden)

### 2. Validação de Segurança (CRÍTICA)

Para PROPERTY_OWNER, **DEVE** validar relação antes de retornar dados:

```python
if current_user.role == RoleEnum.PROPERTY_OWNER:
    if user_id != current_user.id:
        # Chamar API de imóveis para validar
        has_relation = await check_user_property_relation(user_id, current_user.id)
        if not has_relation:
            raise HTTPException(403, "No relation with this user")
```

### 3. Helper Function

```python
async def check_user_property_relation(user_id: UUID, owner_id: UUID) -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{PROPERTIES_API_URL}/api/internal/check-user-property-relation",
            params={"user_id": str(user_id), "owner_id": str(owner_id)},
            headers={"X-Internal-Secret": INTERNAL_API_SECRET}
        )
        
        if response.status_code == 200:
            return response.json().get("has_relation", False)
        return False  # Fail-safe
```

### 4. Variáveis de Ambiente

Adicionar no `.env` do auth service:

```bash
# URL da API de imóveis (interno no Docker)
PROPERTIES_API_URL=http://sexto-andar-properties-api:8000

# Secret compartilhado (deve ser IGUAL nos dois serviços)
INTERNAL_API_SECRET=change-this-to-secure-random-secret-in-production

# JWT Settings (verificar se já existem com estes valores exatos)
JWT_SECRET_KEY=P2M3wtplsZOfysdRFaS9Q2sdi0JAkWY1IstrT4-seqY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ CRÍTICO - Valores Compartilhados:**

Os seguintes secrets **DEVEM SER IDÊNTICOS** nos dois serviços:

| Variável | Valor | Status |
|----------|-------|--------|
| `INTERNAL_API_SECRET` | `change-this-to-secure-random-secret-in-production` | ⚠️ Mudar em produção |
| `JWT_SECRET_KEY` | `P2M3wtplsZOfysdRFaS9Q2sdi0JAkWY1IstrT4-seqY` | ✅ Já configurado |
| `JWT_ALGORITHM` | `HS256` | ✅ Já configurado |

**Nota**: O `INTERNAL_API_SECRET` está com valor temporário de desenvolvimento. Para produção, gerar um novo:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
E atualizar nos dois serviços (.env de ambos).

### 5. Response Model

```python
{
  "id": "uuid",
  "username": "string",
  "fullName": "string",
  "email": "string",
  "phoneNumber": "string | null",
  "role": "USER | PROPERTY_OWNER | ADMIN",
  "createdAt": "ISO8601",
  "isActive": true
}
```

**⚠️ NUNCA retornar**: `password`, `hashed_password`, tokens

---

## 📝 Documentação Completa

Ver arquivo: `docs/AUTH_SERVICE_REQUIRED_ENDPOINT.md`

Contém:
- ✅ Especificação completa da API
- ✅ Código de implementação (controller, service, DTO)
- ✅ Exemplos de uso (cURL, Python)
- ✅ 9 casos de teste obrigatórios
- ✅ Tratamento de erros
- ✅ Considerações de segurança

---

## 🔒 Por que essa implementação é segura?

### ❌ Implementação INSEGURA (não fazer):
```python
# Property owner pode buscar QUALQUER usuário
if current_user.role == RoleEnum.PROPERTY_OWNER:
    # Sem validação - BRECHA DE SEGURANÇA!
    return user_data
```

**Problema**: Proprietário pode fazer scraping de todos os usuários da plataforma.

### ✅ Implementação SEGURA (fazer):
```python
# Property owner só pode buscar usuários relacionados
if current_user.role == RoleEnum.PROPERTY_OWNER:
    has_relation = await check_user_property_relation(...)
    if not has_relation:
        raise HTTPException(403)  # Bloqueado!
    return user_data
```

**Benefício**: Proprietário só acessa dados de quem realmente interagiu com suas propriedades.

---

## 🧪 Como testar após implementação

### 1. Testar endpoint interno da API de imóveis

```bash
# Com secret errado (deve retornar 401)
curl -X GET "http://localhost:8000/api/internal/check-user-property-relation?user_id=xxx&owner_id=yyy" \
  -H "X-Internal-Secret: wrong-secret"

# Com secret correto (deve retornar has_relation)
curl -X GET "http://localhost:8000/api/internal/check-user-property-relation?user_id=xxx&owner_id=yyy" \
  -H "X-Internal-Secret: ${INTERNAL_API_SECRET}"
```

### 2. Testar endpoint do auth

```bash
# Login como admin
curl -X POST http://localhost:8001/auth/login \
  -d '{"username":"admin","password":"senha123"}' -c cookies.txt

# Buscar qualquer usuário (deve funcionar)
curl -X GET http://localhost:8001/auth/admin/users/{user_id} -b cookies.txt

# Login como property owner
curl -X POST http://localhost:8001/auth/login \
  -d '{"username":"johndoe","password":"senha123"}' -c cookies2.txt

# Buscar usuário COM relação (deve funcionar)
curl -X GET http://localhost:8001/auth/admin/users/{visitor_id} -b cookies2.txt

# Buscar usuário SEM relação (deve retornar 403)
curl -X GET http://localhost:8001/auth/admin/users/{random_id} -b cookies2.txt
```

---

## 📊 Casos de Teste Obrigatórios

1. ✅ Admin busca qualquer usuário → 200 OK
2. ✅ Property owner busca próprio ID → 200 OK
3. ✅ Property owner busca visitante → 200 OK (se tem visita)
4. ❌ Property owner busca usuário aleatório → 403 Forbidden
5. ❌ User regular tenta acessar → 403 Forbidden
6. ❌ Sem autenticação → 401 Unauthorized
7. ❌ Usuário não existe → 404 Not Found
8. ✅ Response não contém senha → Verificar
9. ❌ Properties API offline → 403 Forbidden (fail-safe)

---

## 🚀 Próximos passos

1. **No sexto-andar-auth**:
   - [ ] Implementar endpoint `GET /auth/admin/users/{user_id}`
   - [ ] Adicionar validação de relação para PROPERTY_OWNER
   - [ ] Adicionar variáveis PROPERTIES_API_URL e INTERNAL_API_SECRET
   - [ ] Escrever testes
   - [ ] Deploy e teste integrado

2. **No sexto-andar-api** (já feito):
   - [x] Endpoint interno `/api/internal/check-user-property-relation`
   - [x] Configuração INTERNAL_API_SECRET
   - [x] Documentação completa

3. **Integração final**:
   - [ ] Descomentar código em `sexto-andar-api/app/auth/auth_client.py`
   - [ ] Testar US21 end-to-end com dados reais de usuários
   - [ ] Validar que proprietários veem nome/email/telefone dos visitantes

---

## ❓ Dúvidas?

Consultar:
- Documentação completa: `docs/AUTH_SERVICE_REQUIRED_ENDPOINT.md`
- Implementação do endpoint interno: `app/controllers/internal_controller.py`
- Configurações: `app/settings.py` e `.env`
