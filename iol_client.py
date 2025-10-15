import json
import os
import time
from typing import Any, Dict

import requests
from dotenv import load_dotenv

TOKEN_FILE = "tokens.json"


class IOLClient:
    """
    Cliente profesional para la API de InvertirOnline (IOL)
    - Maneja autenticación, refresh token, persistencia y requests autenticadas.
    - Cache de tokens por endpoint.
    - Context manager para inicialización y limpieza automática.
    """

    def __init__(self):
        load_dotenv()
        self.api_url = os.getenv("IOL_API_URL", "https://api.invertironline.com")
        self.username = os.getenv("IOL_USERNAME")
        self.password = os.getenv("IOL_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("Faltan credenciales en el archivo .env")

        self.tokens = self._cargar_tokens()

    # -----------------------------------------------------------
    # Context manager
    # -----------------------------------------------------------
    def __enter__(self):
        # No hace nada especial al entrar
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Persiste todos los tokens al salir
        self._guardar_tokens()

    
    
    # -----------------------------------------------------------
    # 🔐 Manejo de tokens
    # -----------------------------------------------------------
    def _cargar_tokens(self) -> Dict[str, Any]:
        """Carga tokens desde archivo, si existen."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)
                return tokens
        return None

    def _guardar_tokens(self):
        """Guarda tokens en archivo JSON."""
        if self.tokens:
            with open(TOKEN_FILE, "w") as f:
                json.dump(self.tokens, f)

    def _endpoint_key(self, endpoint: str) -> str:
        """Normaliza endpoint para usar como clave en cache."""
        return endpoint.lstrip("/")

    def authenticate(self):
        """Obtiene bearer y refresh tokens usando usuario/contraseña."""
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }

        response = requests.post(f"{self.api_url}/token", data=data)
        response.raise_for_status()

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        return self.tokens

    def refresh_token(self):
        """Refresca el bearer token usando el refresh token."""
        if not self.tokens or "refresh_token" not in self.tokens:
            raise RuntimeError("No hay token para refrescar. Ejecutá authenticate() primero.")

        data = {
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token"
        }

        response = requests.post(f"{self.api_url}/token", data=data)
        response.raise_for_status()

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        return self.tokens

    def token_expired(self) -> bool:
        """Chequea si el bearer token expiró."""
        return not self.tokens or time.time() >= self.tokens.get("expires_at", 0)

    def get_access_token(self) -> str:
        """Devuelve un bearer token válido (refrescando si es necesario)."""
        if self.token_expired():
            if self.tokens and "refresh_token" in self.tokens:
                self.refresh_token()
            else:
                self.authenticate()
        return self.tokens["access_token"]

    # -----------------------------------------------------------
    # 🌐 Requests autenticadas
    # -----------------------------------------------------------
    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def get(self, endpoint: str, params: Dict[str, Any] = None):
        """GET autenticado."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, headers=self._auth_headers(), params=params)
        if response.status_code == 401:
            self.refresh_token()
            response = requests.get(url, headers=self._auth_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None):
        """POST autenticado."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        response = requests.post(url, headers=self._auth_headers(), data=data)
        if response.status_code == 401:
            self.refresh_token()
            response = requests.post(url, headers=self._auth_headers(), data=data)
        response.raise_for_status()
        return response.json()
