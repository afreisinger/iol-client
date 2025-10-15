# IOL Python Client

Cliente en Python para interactuar con la API de InvertirOnline (IOL).

Características:

- Autenticación con usuario y contraseña.
- Manejo de bearer token y refresh token.
- Persistencia automática de tokens en disco (`tokens.json`).
- Refresco automático de tokens al expirar.
- Cache de token por endpoint para mayor eficiencia.
- Context manager (`with IOLClient() as client`) para inicialización y limpieza automática.
- Métodos GET y POST autenticados listos para usar.
- Ideal para estrategias de trading automáticas y consultas frecuentes.

## Instalación

Cloná el repositorio y instalá las dependencias:

```bash
git clone https://github.com/afreisinger/iol-client.git
cd iol-client
pip install -r requirements.txt
```

## Uso

Crear un archivo .env con tus credenciales:

```python
IOL_USERNAME=tu_usuario
IOL_PASSWORD=tu_contraseña
IOL_API_URL=https://api.invertironline.com
```

Crea un archivo main.py por ejemplo

```python

from iol_client import IOLClient

def main():
    iol = IOLClient()
    iol.authenticate()
    data = iol.get("/api/v2/estadocuenta")
    print(data)
if __name__ == "__main__":
    main()
```
