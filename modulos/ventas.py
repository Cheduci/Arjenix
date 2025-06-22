from . import carrito as crt
from datetime import datetime
from . import scaner

def iniciar_venta(cur):
    carrito = []
    print("🛒 Iniciando venta ")

    while True:
        print("[A] Ver  [B] Modificar  [C] Eliminar  [F] Finalizar  [X] Cancelar")
        entrada = input("\n➡️ Presione Enter para escanear o ingrese comando [A/B/C/F/X]: ").strip().upper()

        if entrada == "A":
            crt.mostrar_carrito(carrito)

        elif entrada == "B":
            print("🔄 Código de barra a modificar: ")
            codigo = scaner.obtener_codigo_barra()
            for item in carrito:
                if item["codigo_barra"] == codigo:
                    try:
                        cantidad = int(input("Nueva cantidad (0 para eliminar): "))
                        if cantidad < 0:
                            print("⚠️ No se permiten valores negativos.")
                        elif cantidad == 0:
                            crt.eliminar_del_carrito(carrito, item["producto_id"])
                        else:
                            cur.execute("SELECT stock_actual FROM productos WHERE id = %s;", (item["producto_id"],))
                            stock_actual = cur.fetchone()
                            if stock_actual and cantidad > stock_actual[0]:
                                print(f"⚠️ Stock insuficiente. Solo hay {stock_actual[0]} unidades disponibles.")
                            else:
                                item["cantidad"] = cantidad
                                print(f"✏️ Cantidad de '{item['nombre']}' actualizada a {cantidad}")
                    except ValueError:
                        print("⚠️ Número inválido.")
                    break
            else:
                print("⚠️ Producto no está en el carrito.")
            crt.mostrar_carrito(carrito)

        elif entrada == "C":
            print("🗑️ Código de barra a eliminar: ")
            codigo = scaner.obtener_codigo_barra()
            for item in carrito:
                if item["codigo_barra"] == codigo:
                    crt.eliminar_del_carrito(carrito, item["producto_id"])
                    break
                else:
                    print("⚠️ Producto no encontrado en el carrito.")
            crt.mostrar_carrito(carrito)

        elif entrada == "F":
            if not carrito:
                print("⚠️ El carrito está vacío.")
                continue
            confirmar_venta(cur, carrito)
            break

        elif entrada == "X":
            print("🚫 Venta cancelada.")
            break

        else:
            codigo = scaner.obtener_codigo_barra()
            if not codigo:
                print("⚠️ No se obtuvo ningún código.")
                continue

            cur.execute("""
                SELECT id, nombre, precio_venta, stock_actual
                FROM productos
                WHERE codigo_barra = %s;
            """, (codigo,))
            prod = cur.fetchone()
            if not prod:
                print("❌ Producto no encontrado.")
                continue

            pid, nombre, precio, stock = prod
            print(f"📦 {nombre} | Precio: ${precio:.2f} | Stock disponible: {stock}")

            # Verificar si ya está en el carrito
            item_existente = next((item for item in carrito if item["codigo_barra"] == codigo), None)
            cantidad_actual = item_existente["cantidad"] if item_existente else 0

            if cantidad_actual + 1 > stock:
                print("⚠️ No se puede agregar otra unidad: stock insuficiente.")
                continue

            if item_existente:
                item_existente["cantidad"] += 1
                print(f"➕ Se aumentó en 1 la cantidad de '{item_existente['nombre']}' en el carrito.")
            else:
                crt.agregar_al_carrito(carrito, pid, nombre, precio, 1, codigo_barra=codigo)
                print(f"✅ Se agregó '{nombre}' (1 unidad) al carrito.")

            crt.mostrar_carrito(carrito)


def confirmar_venta(cur, carrito):
    try:
        total = sum(item["cantidad"] * item["precio_unitario"] for item in carrito)
        metodo = input("💳 Método de pago (efectivo / tarjeta / otro): ").strip().lower() or "otro"

        # Insertar cabecera de venta
        cur.execute("""
            INSERT INTO ventas (fecha_hora, total, metodo_pago)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (datetime.now(), total, metodo))
        venta_id = cur.fetchone()[0]

        # Insertar detalle y actualizar stock
        for item in carrito:
            cur.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s);
            """, (venta_id, item["producto_id"], item["cantidad"], item["precio_unitario"]))

            cur.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - %s
                WHERE id = %s;
            """, (item["cantidad"], item["producto_id"]))

        print(f"\n💰 Venta registrada con éxito (ID {venta_id}). Total: ${total:.2f}")
        carrito.clear()

    except Exception as e:
        cur.connection.rollback()
        print(f"❌ Error al registrar la venta: {e}")
    else:
        cur.connection.commit()

