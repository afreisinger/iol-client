# IOL Python Client

Cliente en Python para interactuar con la API de InvertirOnline (IOL).

Características:

- Autenticación con usuario y contraseña.
- Manejo de bearer token y refresh token.
- Persistencia automática de tokens en disco (`tokens.json`).
- Refresco automático de tokens al expirar..
- Métodos GET y POST autenticados listos para usar.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

cCrear un archivo .env con tus credenciales:

```python
IOL_USERNAME=tu_usuario
IOL_PASSWORD=tu_contraseña
IOL_API_URL=https://api.invertironline.com
```

```python
from iol_client import IOLClient

with IOLClient() as client:
    # Obtener estado de cuenta
    data = client.get("/api/v2/estadocuenta")
    print(data)

    # Ejecutar orden (ejemplo)
    # client.post("/api/v2/ordenes", data={"ticker": "GGAL", "cantidad": 10})

```