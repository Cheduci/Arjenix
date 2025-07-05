from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QMessageBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core import productos
from bbdd import db_config
import os

class FichaProductoDialog(QDialog):
    def __init__(self, sesion: dict, codigo: str):
        super().__init__()
        self.sesion = sesion
        self.codigo = codigo
        self.setWindowTitle(f"📄 Ficha del producto — {codigo}")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.cargar_datos()
        self.mensaje_mostrado = False

    def setup_ui(self):
        self.layout = QVBoxLayout()

        # 🖼️ Imagen
        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.imagen)

        # 📝 Nombre
        self.nombre = QLabel()
        self.layout.addWidget(self.nombre)

        # 📦 Código y categoría
        self.codigo_label = QLabel()
        self.layout.addWidget(self.codigo_label)

        # 🧾 Descripción
        self.descripcion = QTextEdit()
        self.descripcion.setReadOnly(True)
        self.layout.addWidget(self.descripcion)

        # 📊 Stock
        stock_layout = QHBoxLayout()
        stock_layout.addWidget(QLabel("Stock:"))
        self.campo_stock = QSpinBox()
        self.campo_stock.setRange(0, 100000)
        self.campo_stock.setEnabled(False)  # Se activará si el rol lo permite
        stock_layout.addWidget(self.campo_stock)
        self.layout.addLayout(stock_layout)

        # 💰 Precios
        precio_layout = QHBoxLayout()
        self.precio_compra = QDoubleSpinBox()
        self.precio_compra.setPrefix("$")
        self.precio_compra.setMaximum(999999)
        self.precio_compra.setDecimals(2)
        self.precio_compra.setEnabled(False)

        self.precio_venta = QDoubleSpinBox()
        self.precio_venta.setPrefix("$")
        self.precio_venta.setMaximum(999999)
        self.precio_venta.setDecimals(2)
        self.precio_venta.setEnabled(False)

        precio_layout.addWidget(QLabel("Precio compra:"))
        precio_layout.addWidget(self.precio_compra)
        precio_layout.addWidget(QLabel("Precio venta:"))
        precio_layout.addWidget(self.precio_venta)
        self.layout.addLayout(precio_layout)

        # 🔘 Botones
        self.btn_guardar_stock = QPushButton("Actualizar stock")
        self.btn_guardar_precios = QPushButton("Actualizar precios")
        self.btn_inactivar = QPushButton("Inactivar producto")
        self.btn_reactivar = QPushButton("Reactivar")
        self.btn_eliminar = QPushButton("Eliminar permanentemente")

        # Vínculos a eventos (a definir)
        self.btn_guardar_stock.clicked.connect(self.actualizar_stock)
        self.btn_guardar_precios.clicked.connect(self.actualizar_precios)
        self.btn_inactivar.clicked.connect(self.inactivar_producto)
        self.btn_reactivar.clicked.connect(self.reactivar_producto)
        self.btn_eliminar.clicked.connect(self.eliminar_producto)

        # Se agregan dinámicamente según el rol
        self.layout.addStretch()
        self.setLayout(self.layout)

    def cargar_datos(self):
        producto = productos.obtener_producto_por_codigo(self.codigo)
        if not producto:
            QMessageBox.critical(self, "Error", "No se pudo cargar el producto.")
            self.reject()
            return

        # 📄 Info básica
        self.nombre.setText(f"<h2>{producto['nombre']}</h2>")
        if not producto["activo"]:
            self.nombre.setText(
                f"<h2 style='color:gray'>{producto['nombre']} (INACTIVO)</h2>"
            )

            if not self.mensaje_mostrado:
                QMessageBox.information(
                    self,
                    "Producto inactivo",
                    "⚠️ Este producto está actualmente inactivo.\nNo puede ser vendido ni utilizado en operaciones.",
                    QMessageBox.StandardButton.Ok
                )
                self.mensaje_mostrado = True

        self.codigo_label.setText(f"Código: {producto['codigo']} — Categoría: {producto['categoria']}")
        self.descripcion.setText(producto["descripcion"])
        self.campo_stock.setValue(producto["stock"])
        self.precio_compra.setValue(producto["precio_compra"])
        self.precio_venta.setValue(producto["precio_venta"])

        # 🖼️ Imagen si existe
        ruta_foto = producto.get("foto")
        if ruta_foto and os.path.exists(ruta_foto):
            pixmap = QPixmap(ruta_foto).scaled(200, 200, Qt.KeepAspectRatio)
            self.imagen.setPixmap(pixmap)
        else:
            self.imagen.setText("📷 Sin imagen")

        # 🔒 Permisos según rol
        rol = self.sesion["rol"]

        if rol in ["dueño", "gerente", "depositor"]:
            self.campo_stock.setEnabled(True)
            self.layout.addWidget(self.btn_guardar_stock)

        if rol in ["dueño", "gerente"]:
            self.precio_compra.setEnabled(True)
            self.precio_venta.setEnabled(True)
            self.layout.addWidget(self.btn_guardar_precios)

        if rol in ["dueño", "gerente"] and producto["activo"]:
            self.layout.addWidget(self.btn_inactivar)

        if rol in ["dueño", "gerente"] and not producto["activo"]:
            self.layout.addWidget(self.btn_reactivar)

        if rol == "dueño":
            self.layout.addWidget(self.btn_eliminar)

    # Métodos a definir para acciones:
    def actualizar_stock(self): 
        nuevo_stock = self.campo_stock.value()

        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Actualizar el stock del producto a {nuevo_stock} unidades?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        ok = productos.modificar_stock(self.codigo, nuevo_stock)

        if ok:
            QMessageBox.information(self, "Éxito", "✅ Stock actualizado correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el stock.")

    def actualizar_precios(self): 
        compra = self.precio_compra.value()
        venta = self.precio_venta.value()

        if compra > venta:
            QMessageBox.warning(self, "Precios inconsistentes", "El precio de venta no puede ser menor que el de compra.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Actualizar los precios?\nCompra: ${compra:.2f}\nVenta: ${venta:.2f}",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        ok = productos.actualizar_precios(self.codigo, compra, venta)

        if ok:
            QMessageBox.information(self, "Éxito", "✅ Precios actualizados correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron actualizar los precios.")
        
    def inactivar_producto(self): 
        respuesta = QMessageBox.question(
            self, "Confirmar",
            "¿Estás seguro de que querés inactivar este producto?\nPodrás reactivarlo luego.",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta != QMessageBox.Yes:
            return

        ok = productos.inactivar_producto(self.codigo)
        if ok:
            QMessageBox.information(self, "Hecho", "🟡 Producto inactivado.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo inactivar el producto.")
    
    def reactivar_producto(self):
        respuesta = QMessageBox.question(
            self, "Confirmar",
            "¿Querés reactivar este producto y volverlo disponible?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta != QMessageBox.Yes:
            return

        ok = productos.reactivar_producto(self.codigo)
        if ok:
            QMessageBox.information(self, "Reactivado", "🟢 Producto reactivado.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo reactivar el producto.")
    
    def eliminar_producto(codigo: str) -> bool: 
        try:
            conn = db_config.conectar_db()
            cur = conn.cursor()

            # ⚠️ Ideal: chequear dependencias antes
            cur.execute("DELETE FROM productos WHERE codigo = %s", (codigo,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al eliminar producto: {e}")
            return False
        
    