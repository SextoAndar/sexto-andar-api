import os
from typing import List
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()


class Settings:
    """
    Configurações da aplicação - lê variáveis de ambiente com valores base.
    
    IMPORTANTE: AUTH_SERVICE_URL é OBRIGATÓRIO para funcionamento da aplicação.
    Este repositório delega 100% da autenticação para sexto-andar-auth.
    """
    
    # Valores base (padrão)
    _API_BASE_PATH: str = "/api"
    _API_VERSION: str = "v1"
    _ADMIN_ROUTE: str = "/admin"
    _ALLOW_ORIGINS: List[str] = ["*"]
    _DEBUG: bool = False
    
    def __init__(self):
        """Inicializa configurações lendo do .env se disponível."""
        # API
        self.API_BASE_PATH: str = os.getenv("API_BASE_PATH", self._API_BASE_PATH)
        self.API_VERSION: str = os.getenv("API_VERSION", self._API_VERSION)
        
    # Rotas
    # NOTE: AUTH_ROUTE was removed because authentication is fully delegated
    # to the external `sexto-andar-auth` service. Keep ADMIN_ROUTE for any
    # admin-related endpoints if this repo exposes them.
    self.ADMIN_ROUTE: str = os.getenv("ADMIN_ROUTE", self._ADMIN_ROUTE)
        
        # CORS - parse comma-separated string ou use default
        origins_str = os.getenv("ALLOW_ORIGINS", "*")
        self.ALLOW_ORIGINS: List[str] = [o.strip() for o in origins_str.split(",")] if origins_str else self._ALLOW_ORIGINS
        
        # Debug
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # Serviço remoto de autenticação - OBRIGATÓRIO
        self.AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "").strip()
        
        if not self.AUTH_SERVICE_URL:
            raise ValueError(
                "❌ AUTH_SERVICE_URL não configurado!\n"
                "Este serviço delega 100% da autenticação para sexto-andar-auth.\n"
                "Configure a variável de ambiente AUTH_SERVICE_URL.\n"
                "Exemplo: AUTH_SERVICE_URL=http://localhost:8001"
            )
    
    @property
    def root_prefix(self) -> str:
        """Retorna o prefixo base da API, ex: /api/v1"""
        base = self.API_BASE_PATH.rstrip('/')
        version = self.API_VERSION.strip('/')
        return f"{base}/{version}"
    
    def api_route(self, route: str) -> str:
        """Compõe uma rota completa combinando root_prefix + rota."""
        if not route:
            return self.root_prefix
        return f"{self.root_prefix.rstrip('/')}/{route.lstrip('/')}"


# Instância global
settings = Settings()
