from iol_client import IOLClient

def main():
    iol = IOLClient()

    # Autenticarse (se hace automáticamente si no hay token válido)
    print("🔐 Autenticando con IOL...")
    iol.authenticate()

    # Ejemplo: obtener estado de cuenta
    print("📊 Obteniendo estado de cuenta...")
    data = iol.get("/api/v2/estadocuenta")
    print(data)

if __name__ == "__main__":
    main()
