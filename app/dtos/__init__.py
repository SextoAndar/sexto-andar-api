# app/dtos/__init__.py
"""
Data Transfer Objects (DTOs) - autenticação delegada para sexto-andar-auth.

DTOs relacionados a autenticação (LoginRequest, RegisterRequest, etc)
não devem ser definidos aqui - use os endpoints do serviço remoto.

DTOs deste repositório devem focar em domínios de negócio:
- PropertyDTO
- VisitDTO  
- ProposalDTO
- AddressDTO
etc.

Exemplo de DTO de domínio:

    from pydantic import BaseModel
    from datetime import datetime
    from typing import Optional
    
    class PropertyDTO(BaseModel):
        id: str
        title: str
        description: Optional[str]
        price: float
        created_at: datetime
        
        class Config:
            from_attributes = True
"""
