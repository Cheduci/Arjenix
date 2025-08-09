from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget
from typing import Literal
from modulos import camara

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

def flujo_escaneo_codigo(parent: QWidget) -> str | None:
    while True:
        codigo = camara.escanear_codigo_opencv()  # Tu función personalizada
        if not codigo:
            QMessageBox.warning(parent, "Error", "No se detectó ningún código.")
            return None

        respuesta = QMessageBox.question(
            parent,
            "Confirmar código",
            f"Código detectado: {codigo}\n¿Es correcto?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            return codigo.strip()

def flujo_ingreso_manual_codigo(parent: QWidget) -> str | None:
    while True:
        texto, ok = QInputDialog.getText(parent, "Ingresar código", "Código de barras:")
        if not ok:
            return None

        respuesta = QMessageBox.question(
            parent,
            "Confirmar código",
            f"Código ingresado: {texto}\n¿Es correcto?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            return texto.strip()
        
def obtener_codigo(parent: QWidget, modo: Literal["manual", "escanear"], codigo_actual: str | None = None) -> str | None:
    flujo = flujo_ingreso_manual_codigo if modo == "manual" else flujo_escaneo_codigo
    codigo = flujo(parent)
    if not codigo:
        return None
    if codigo == codigo_actual:
        QMessageBox.information(parent, "Código duplicado", "Este código ya fue ingresado.")
        return None
    return codigo
