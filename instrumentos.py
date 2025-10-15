from iol_client import IOLClient


def main():
    # Instanciamos el cliente
    with IOLClient() as iol:
        print("🔐 Autenticando con IOL...")
        iol.authenticate()

        # La autenticación se hace automáticamente si no hay token válido

        # ------------------------------
        # 1️⃣ Estado de cuenta
        # ------------------------------
        print("\n📊 Obteniendo estado de cuenta...")
        estado = iol.get("/api/v2/estadocuenta")
        print(estado)

        # ------------------------------
        # 2️⃣ Portafolio
        # ------------------------------
        # print("\n💼 Obteniendo portafolio...")
        # portafolio = iol.get("/api/v2/portafolio")
        # print(portafolio)

        # ------------------------------
        # 3️⃣ Cotizaciones de múltiples instrumentos
        # ------------------------------
        instrumentos = ["ACCIONES"]
        pais = "ARGENTINA"

        for ins in instrumentos:
            endpoint = f"/api/v2/Cotizaciones/{ins}/{pais}/Todos"
            print(f"\n📈 Consultando {ins} en {pais}...")
            data = iol.get(endpoint)

            titulos = data.get("titulos", [])
            if not titulos:
                print("No se encontraron títulos para este instrumento.")
                continue

        for titulo in titulos:
            print(f"\nSímbolo: {titulo.get('simbolo')}")
            print(f"Descripción: {titulo.get('descripcion')}")
            print(f"Último precio: {titulo.get('ultimoPrecio')}")
            print(f"Variación %: {titulo.get('variacionPorcentual')}")
            print(f"Apertura: {titulo.get('apertura')}")
            print(f"Máximo: {titulo.get('maximo')}")
            print(f"Mínimo: {titulo.get('minimo')}")
            print(f"Último cierre: {titulo.get('ultimoCierre')}")
            print(f"Volumen: {titulo.get('volumen')}")
            print(f"Cantidad de operaciones: {titulo.get('cantidadOperaciones')}")
            print(f"Tipo de opción: {titulo.get('tipoOpcion')}")
            print(f"Precio ejercicio: {titulo.get('precioEjercicio')}")
            print(f"Fecha vencimiento: {titulo.get('fechaVencimiento')}")
            print(f"Mercado: {titulo.get('mercado')}")
            print(f"Moneda: {titulo.get('moneda')}")

            if titulo.get("puntas"):
                print(f"Punta compra: {titulo['puntas'].get('precioCompra')} x {titulo['puntas'].get('cantidadCompra')}")
                print(f"Punta venta: {titulo['puntas'].get('precioVenta')} x {titulo['puntas'].get('cantidadVenta')}")

            
if __name__ == "__main__":
    main()
