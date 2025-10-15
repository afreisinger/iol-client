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

    # Ejemplo: múltiples endpoints
    print("\n📈 Obteniendo portafolio y cotizaciones...")
    portafolio = iol.get("/api/v2/portafolio")
    #cotizaciones = iol.get("/api/v2/cotizaciones", params={"tickers": "GGAL,YPFD,BMA"})

    print("Portafolio:")
    print(portafolio)

if __name__ == "__main__":
    main()
