from PySide6.QtWidgets import QInputDialog

def solicitar_cantidad(parent, descripcion="producto", stock=99) -> int:
    cantidad, ok = QInputDialog.getInt(
        parent,
        "Cantidad",
        f"Cantidad de unidades de '{descripcion}' a agregar:",
        1,  # valor predeterminado
        1,  # mínimo
        stock  # máximo
    )
    return cantidad if ok else None

def pedir_codigo_barras(parent=None):
    codigo, ok = QInputDialog.getText(parent, "Ingreso manual", "📦 Ingresá el código de barras:")
    if not ok or not codigo:
        return None

    codigo = codigo.strip()
    if len(codigo) == 13 and codigo.isdigit():
        codigo = codigo[:12]  # Quitar dígito de control

    return codigo