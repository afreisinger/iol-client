import json
import os
import time
import logging
import requests
from typing import Any, Dict
from dotenv import load_dotenv
from rich.logging import RichHandler

TOKEN_FILE = "tokens.json"

# -----------------------------------------------------------
# 📜 Configuración básica de logging
# -----------------------------------------------------------
log_level = os.getenv("IOL_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),  # Cambiá a DEBUG para más detalle
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger("IOLClient")

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
        logger.debug(f"[cyan]Cliente inicializado con endpoint[/cyan] {self.api_url}")


    # -----------------------------------------------------------
    # Context manager
    # -----------------------------------------------------------
    def __enter__(self):
        # No hace nada especial al entrar
        logger.info("[green]🔑 Iniciando sesión con IOLClient...[/green]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Persiste todos los tokens al salir
        self._guardar_tokens()
        if exc_type:
            logger.error(f"[red]Ocurrió un error:[/red] {exc_type.__name__} - {exc_val}")

    
    
    # -----------------------------------------------------------
    # 🔐 Manejo de tokens
    # -----------------------------------------------------------
    def _cargar_tokens(self) -> Dict[str, Any]:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)
                logger.info("[green]✅ Tokens cargados desde archivo.[/green]")
                return tokens
        logger.info("[yellow]ℹ️ No se encontraron tokens guardados.[/yellow]")
        return None

    def _guardar_tokens(self):
        if self.tokens:
            with open(TOKEN_FILE, "w") as f:
                json.dump(self.tokens, f)
            logger.info("[green]💾 Tokens guardados correctamente.[/green]")

    def authenticate(self):
        logger.info("[blue]🔐 Autenticando usuario en IOL...[/blue]")
        logger.debug(f"[blue]Usuario:[/blue] {self.username}")
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }

        try:
            response = requests.post(f"{self.api_url}/token", data=data)
            response.raise_for_status()  # lanza HTTPError si status != 2xx
        except requests.HTTPError as e:
            # Mostrar mensaje amigable y loguear
            status = e.response.status_code if e.response else "Desconocido"
            text = e.response.text if e.response else ""
            logger.error(f"[red]❌ Error de autenticación (status {status}):[/red] {text}")
            raise  # opcional: relanza para que el flujo principal también lo vea

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        logger.info("[green]✅ Autenticación exitosa.[/green]")
        return self.tokens

    def refresh_token(self):
        if not self.tokens or "refresh_token" not in self.tokens:
            raise RuntimeError("No hay token para refrescar. Ejecutá authenticate() primero.")

        logger.info("[cyan]♻️  Refrescando token...[/cyan]")
        data = {
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token"
        }

        response = requests.post(f"{self.api_url}/token", data=data)
        response.raise_for_status()

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        logger.info("[green]✅ Token refrescado correctamente.[/green]")
        return self.tokens

    def refresh_token(self):
        if not self.tokens or "refresh_token" not in self.tokens:
            raise RuntimeError("No hay token para refrescar. Ejecutá authenticate() primero.")

        logger.info("[cyan]♻️  Refrescando token...[/cyan]")
        data = {
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token"
        }

        response = requests.post(f"{self.api_url}/token", data=data)
        response.raise_for_status()

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        logger.info("[green]✅ Token refrescado correctamente.[/green]")
        return self.tokens
  
    def token_expired(self) -> bool:
        expired = not self.tokens or time.time() >= self.tokens.get("expires_at", 0)
        if expired:
            logger.debug("[yellow]⚠️  El token ha expirado o no existe.[/yellow]")
        return expired

    def get_access_token(self) -> str:
        if self.token_expired():
            if self.tokens and "refresh_token" in self.tokens:
                self.refresh_token()
            else:
                self.authenticate()
        return self.tokens["access_token"]

    # -----------------------------------------------------------
    # Requests autenticadas
    # -----------------------------------------------------------
    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def get(self, endpoint: str, params: Dict[str, Any] = None):
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        logger.info(f"[cyan]🌐 GET[/cyan] {url}")
        response = requests.get(url, headers=self._auth_headers(), params=params)
        if response.status_code == 401:
            logger.warning("[yellow]⚠️  Token inválido, intentando refrescar...[/yellow]")
            self.refresh_token()
            response = requests.get(url, headers=self._auth_headers(), params=params)
        response.raise_for_status()
        logger.debug(f"[green]✅ GET {endpoint} OK[/green]")
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None):
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        logger.info(f"[magenta]📤 POST[/magenta] {url}")
        response = requests.post(url, headers=self._auth_headers(), data=data)
        if response.status_code == 401:
            logger.warning("[yellow]⚠️  Token inválido, intentando refrescar...[/yellow]")
            self.refresh_token()
            response = requests.post(url, headers=self._auth_headers(), data=data)
        response.raise_for_status()
        logger.debug(f"[green]✅ POST {endpoint} OK[/green]")
        return response.json()
