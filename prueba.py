from modulos.carrito import *

def gestionar_carrito():
    carrito = []

    while True:
        print("\n=== MENÚ CARRITO ===")
        print("[1] Agregar producto")
        print("[2] Eliminar producto")
        print("[3] Mostrar carrito")
        print("[0] Salir")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            try:
                prod_id = int(input("ID producto: "))
                nombre = input("Nombre producto: ")
                precio = float(input("Precio unitario: "))
                cantidad = int(input("Cantidad: "))
                agregar_al_carrito(carrito, prod_id, nombre, precio, cantidad)
                mostrar_carrito(carrito)
            except ValueError:
                print("⚠️ Ingresá valores válidos.")
        elif opcion == "2":
            try:
                prod_id = int(input("ID del producto a eliminar: "))
                eliminar_del_carrito(carrito, prod_id)
            except ValueError:
                print("⚠️ Ingresá un número válido.")
        elif opcion == "3":
            mostrar_carrito(carrito)
        elif opcion == "0":
            print("👋 Fin de prueba del carrito.")
            break
        else:
            print("❌ Opción inválida.")

def modo_venta():
    carrito = []
    print("🛒 Iniciando venta. Ingrese productos. Comandos: mod / del / fin / can")

    while True:
        entrada = input("\n➡️  Ingrese ID del producto o comando: ").strip().lower()

        if entrada == "mod":
            try:
                pid = int(input("🔢 ID a modificar: "))
                nueva_cant = int(input("✏️  Nueva cantidad: "))
                for item in carrito:
                    if item["producto_id"] == pid:
                        item["cantidad"] = nueva_cant
                        print(f"✏️  Actualizada cantidad de '{item['nombre']}' a {nueva_cant}")
                        break
                else:
                    print("⚠️ Producto no encontrado.")
            except ValueError:
                print("⚠️ Valor inválido.")

        elif entrada == "del":
            try:
                pid = int(input("🗑️ ID a eliminar: "))
                eliminar_del_carrito(carrito, pid)
            except ValueError:
                print("⚠️ Valor inválido.")

        elif entrada == "fin":
            print("\n✅ Venta completada. Resumen final:")
            mostrar_carrito(carrito)
            break

        elif entrada == "can":
            print("🚫 Venta cancelada. Carrito descartado.")
            break

        else:
            try:
                prod_id = int(entrada)
                nombre = input("📦 Nombre producto: ")
                precio = float(input("💲 Precio unitario: "))
                cantidad = int(input("🔢 Cantidad: "))
                agregar_al_carrito(carrito, prod_id, nombre, precio, cantidad)
                mostrar_carrito(carrito)
            except ValueError:
                print("⚠️ Datos inválidos. Intente de nuevo.")

if __name__ == "__main__":
    modo_venta()

