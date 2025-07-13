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
