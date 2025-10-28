# app/controllers/__init__.py
"""
Controllers - autenticação delegada para sexto-andar-auth.

Este módulo está vazio porque toda gerência de autenticação e contas
é responsabilidade do serviço remoto.

Controllers futuros devem focar em domínios de negócio:
- Properties
- Visits  
- Proposals
- etc

Exemplo de como estruturar um novo controller:

    from fastapi import APIRouter, Depends
    from app.settings import settings
    
    router = APIRouter(tags=["properties"])
    
    @router.get("/properties", summary="List properties")
    async def list_properties(
        current_user: str = Depends(get_current_user),  # Validação delegada
        db: Session = Depends(get_db)
    ):
        # Sua lógica de negócio aqui
        pass
"""
