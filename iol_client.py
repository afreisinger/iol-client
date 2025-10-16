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
# Configuración básica de logging
# -----------------------------------------------------------

# Carga variables de entorno (.env)
load_dotenv()

# Nivel por defecto: INFO (se puede cambiar por .env o argumento)
log_level = os.getenv("IOL_LOG_LEVEL", "INFO").upper()

# Configuración base (solo se ejecuta una vez)
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)

# Logger global del cliente
logger = logging.getLogger("IOLClient")

class IOLClient:
    """
    Cliente profesional para la API de InvertirOnline (IOL)
    - Maneja autenticación, refresh token, persistencia y requests autenticadas.
    - Cache de tokens por endpoint.
    - Context manager para inicialización y limpieza automática.
    """

    # def __init__(self, api_url=None, username=None, password=None, log_level=None):
    #     load_dotenv()
    #     self.api_url = api_url or os.getenv("IOL_API_URL")
    #     self.username = username or os.getenv("IOL_USERNAME")
    #     self.password = password or os.getenv("IOL_PASSWORD")
    #     self.log_level = log_level or os.getenv("IOL_LOG_LEVEL", "INFO").upper()

    #     if not self.username or not self.password:
    #         raise ValueError("Faltan credenciales en el archivo .env")

    #     self.tokens = self._cargar_tokens()
    #     logger.debug(f"[cyan]Cliente inicializado con endpoint[/cyan] {self.api_url}")

    def __init__(self, api_url=None, username=None, password=None, log_level=None):
        load_dotenv()
        self.api_url = api_url or os.getenv("IOL_API_URL")
        self.username = username or os.getenv("IOL_USERNAME")
        self.password = password or os.getenv("IOL_PASSWORD")
        self.log_level = log_level or os.getenv("IOL_LOG_LEVEL", "INFO").upper()

        if not self.username or not self.password:
                raise ValueError("Faltan credenciales en el archivo .env o en los argumentos.")

        # Ajustar nivel de log dinámicamente (por instancia)
        logger.setLevel(getattr(logging, self.log_level, logging.INFO))
        logger.debug(f"[cyan]Logger configurado con nivel {self.log_level}[/cyan]")

        # Ejemplo de log inicial
        logger.debug(f"[cyan]Cliente inicializado con endpoint:[/cyan] {self.api_url}")
  
  
    # -----------------------------------------------------------
    # Context manager
    # -----------------------------------------------------------
    def __enter__(self):
        # No hace nada especial al entrar
        logger.debug("[green]🔑 Iniciando sesión con IOLClient...[/green]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Persiste todos los tokens al salir
        self._guardar_tokens()
        if exc_type:
            logger.error(f"[red]Ocurrió un error:[/red] {exc_type.__name__} - {exc_val}")
        return False  # No suprime excepciones

    
    
    # -----------------------------------------------------------
    # 🔐 Manejo de tokens
    # -----------------------------------------------------------
    def _cargar_tokens(self) -> Dict[str, Any]:
        """Carga tokens desde archivo, si existen."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)
                logger.debug("[green]✅ Tokens cargados desde archivo.[/green]")
                return tokens
        logger.debug("[yellow]ℹ️ No se encontraron tokens guardados.[/yellow]")
        return None

    def _guardar_tokens(self):
        """Guarda tokens en archivo JSON."""
        if self.tokens:
            with open(TOKEN_FILE, "w") as f:
                json.dump(self.tokens, f, indent=2)
            logger.debug("[green]💾 Tokens guardados correctamente.[/green]")

    def authenticate(self):
        """Obtiene bearer y refresh tokens usando usuario/contraseña."""
        logger.debug("[blue]🔐 Autenticando usuario en IOL...[/blue]")
        logger.debug(f"[blue]🔑 Usuario:[/blue] {self.username}")
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
        logger.debug("[green]✅ Autenticación exitosa.[/green]")
        return self.tokens

    def refresh_token(self):
        """Refresca el bearer token usando el refresh token."""
        if not self.tokens or "refresh_token" not in self.tokens:
            raise RuntimeError("No hay token para refrescar. Ejecutá authenticate() primero.")

        logger.debug("[cyan]♻️  Refrescando token...[/cyan]")
        data = {
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token"
        }

        response = requests.post(f"{self.api_url}/token", data=data)
        response.raise_for_status()

        self.tokens = response.json()
        self.tokens["expires_at"] = time.time() + self.tokens["expires_in"]
        self._guardar_tokens()
        logger.debug("[green]✅ Token refrescado correctamente.[/green]")
        return self.tokens
  
    def token_expired(self) -> bool:
        """Chequea si el bearer token expiró."""
        expired = not self.tokens or time.time() >= self.tokens.get("expires_at", 0)
        if expired:
            logger.debug("[yellow]⚠️  El token ha expirado o no existe.[/yellow]")
        return expired

    def get_access_token(self) -> str:
        """Devuelve un bearer token válido (refrescando si es necesario)."""
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
        """GET autenticado."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        logger.debug(f"[cyan]🌐 GET[/cyan] {url}")

        try:
            response = requests.get(url, headers=self._auth_headers(), params=params)
            if response.status_code == 401:
                logger.warning("[yellow]⚠️  Token inválido, intentando refrescar...[/yellow]")
                self.refresh_token()
                response = requests.get(url, headers=self._auth_headers(), params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[red]❌ Error en GET {endpoint}:[/red] {e}")
            raise

        logger.debug(f"[green]✅ GET {endpoint} OK[/green]")
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None):
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        logger.debug(f"[magenta]📤 POST[/magenta] {url}")
        
        try:
            response = requests.post(url, headers=self._auth_headers(), data=data)
            if response.status_code == 401:
                logger.warning("[yellow]⚠️  Token inválido, intentando refrescar...[/yellow]")
                self.refresh_token()
                response = requests.post(url, headers=self._auth_headers(), data=data)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[red]❌ Error en POST {endpoint}:[/red] {e}")
            raise

        logger.debug(f"[green]✅ POST {endpoint} OK[/green]")
        return response.json()

