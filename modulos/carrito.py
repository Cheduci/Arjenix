def mostrar_carrito(carrito):
    if not carrito:
        print("🛒 Carrito vacío.")
        return

    print("\n🧾 Carrito de compra:")
    print(f"{'ID':>3} | {'Nombre':<25} | {'Cant.':>5} | {'P. Unit':>8} | {'Subtotal':>10}")
    print("-" * 60)

    total = 0
    for item in carrito:
        subtotal = item["cantidad"] * item["precio_unitario"]
        total += subtotal
        print(f"{item['producto_id']:>3} | {item['nombre']:<25} | {item['cantidad']:>5} | ${item['precio_unitario']:>7.2f} | ${subtotal:>9.2f}")

    print("-" * 60)
    print(f"{'Total:':>47} ${total:>9.2f}")

def agregar_al_carrito(carrito, producto_id, nombre, precio_unitario, cantidad, codigo_barra):
    for item in carrito:
        if item["producto_id"] == producto_id:
            item["cantidad"] += cantidad
            print(f"🛒 Se agregaron {cantidad} unidades más de '{nombre}' al carrito.")
            return
    carrito.append({
        "producto_id": producto_id,
        "nombre": nombre,
        "precio_unitario": precio_unitario,
        "cantidad": cantidad,
        "codigo_barra": codigo_barra,
    })
    print(f"✅ Producto '{nombre}' agregado al carrito.")

def eliminar_del_carrito(carrito, producto_id):
    for i, item in enumerate(carrito):
        if item["producto_id"] == producto_id:
            del carrito[i]
            print(f"🗑️ Producto '{item['nombre']}' eliminado del carrito.")
            return
    print("⚠️ Producto no encontrado en el carrito.")

def probando():
    print("🔍 Probando funciones del carrito...")