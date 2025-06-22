from modulos.setup_db import *
from modulos.stocker import *
from modulos.reportes import generar_reporte_ventas_pdf
from modulos.ventas import iniciar_venta

def menu():
    print("\n🛍️  GESTOR DE TIENDA")
    print("═════════════════════════")
    print("[1] Agregar producto")
    print("[2] Consultar stock")
    print("[3] Vender")
    print("[4] Modificar un producto")
    print("[5] Eliminar un producto")
    print("[0] Salir")
    return input("\nSeleccione una opción: ").strip()

if __name__ == "__main__":
    if not existe_db():
        crear_db()
    conexion = conectar_db()

    create_table(conexion)

    while True:
        opcion = menu()
        with conexion.cursor() as cur:
            if opcion == "0":
                generar_reporte_ventas_pdf(cur)
                print("👋 Cerrando el programa...")
                break

            if opcion == "1":
                datos = solicitar_datos_producto(cur)
                insertar_producto(cur, datos)
                conexion.commit()

            elif opcion == "2":
                consultar_productos(cur)

            elif opcion == "3":
                iniciar_venta(cur)
                
            elif opcion == "4":
                modificar_producto(cur)

            elif opcion == "5":
                eliminar_producto(cur)

            else:
                print("❌ Opción inválida. Ingrese 0, 1, 2 o 3.")

    conexion.close()
