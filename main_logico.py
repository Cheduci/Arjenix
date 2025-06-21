from modulos.stocker import *

def menu():
    print("\n🛍️  GESTOR DE TIENDA")
    print("═════════════════════════")
    print("[1] Agregar producto")
    print("[2] Consultar stock")
    print("[3] Vender (próximamente)")
    print("[0] Salir")
    return input("Seleccione una opción: ").strip()

if __name__ == "__main__":
    if not existe_db():
        crear_db()
    conexion = conectar_db()

    create_table(conexion)

    while True:
        opcion = menu()
        if opcion == "0":
            print("👋 Cerrando el programa...")
            break

        with conexion.cursor() as cur:
            if opcion == "1":
                datos = solicitar_datos_producto(cur)
                insertar_producto(cur, datos)
                conexion.commit()

            elif opcion == "2":
                consultar_productos(cur)

            elif opcion == "3":
                print("🛒 Función de venta aún no implementada.")

            else:
                print("❌ Opción inválida. Ingrese 0, 1, 2 o 3.")

    conexion.close()
