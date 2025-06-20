from modulos.stocker import *
from modulos.config import *



conexion = connect_to_db()
if conexion:
    print("\n¡Ya tienes una conexión válida para trabajar con tu base de datos!")   
    if not table_exists(conexion):
        create_table(conexion)
    else:
        print(f"La tabla 'productos' ya existe en la base de datos {BD_name}.")

    # while True:
    #     print("\n--- Menú Principal ---")
    #     print("1. Agregar Producto")
    #     print("2. Actualizar Producto")
    #     print("3. Eliminar Producto")
    #     print("4. Consultar Productos")
    #     print("0. Salir")

    #     opcion = input("Seleccione una opción: ")

    #     if opcion == "1":
    #         datos = solicitar_datos_producto()
    #         new_product(conexion, datos)
    #     elif opcion == "2":
    #         print("Actualizar Producto")
    #     elif opcion == "3":
    #         print("Eliminar Producto")
    #     elif opcion == "4":
    #         print("Consultar Productos")
    #     elif opcion == "0":
    #         print("Saliendo del programa...")
    #         break
    #     else:
    #         print("Opción no válida, por favor intente de nuevo.")

else:
    print("No se pudo establecer una conexión con la base de datos. Verifica los detalles de conexión.")