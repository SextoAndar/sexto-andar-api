# app/auth/__init__.py
"""
Módulo de autenticação - delegado 100% para sexto-andar-auth.

Este módulo apenas contém dependências para extrair user_id do token validado
remotamente. Toda lógica de JWT, hash de senha, etc é gerenciada pelo serviço
remoto.
"""
from .dependencies import *
