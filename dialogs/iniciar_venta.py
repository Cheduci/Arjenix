from dialogs.buscar_producto import BuscarProductoDialog
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QWidget, QSpacerItem, QSizePolicy,
    QInputDialog, QMessageBox, 
)
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QUrl, Qt, QTimer
from modulos.camara_thread import CamaraLoopThread
from core import productos
from pathlib import Path
from helpers.dialogos import solicitar_cantidad
from core.ventas import registrar_venta



class IniciarVentaDialog(QDialog):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("🛒 Iniciar venta")
        self.setMinimumSize(960, 600)
        self.carrito = []
        self.camara_loop = None  # Hilo de cámara
        self.beep = QSoundEffect()
        self.beep.setSource(QUrl.fromLocalFile(Path("sonidos/beep.wav")))
        self.beep.setVolume(0.9)

        self.setup_ui()

    def closeEvent(self, event):
        if self.camara_loop and self.camara_loop.isRunning():
            self.detener_escaneo()  # Cerrás hilo y limpiás interfaz
        event.accept()          # Permitís el cierre de la ventana

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 🧾 Izquierda: productos escaneados
        izquierda = QVBoxLayout()

        # --- Preview de cámara ---
        self.lbl_preview = QLabel("Cámara desactivada")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setFixedSize(320, 240)  # Ajusta el tamaño si lo deseas
        izquierda.addWidget(self.lbl_preview)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio u.", "Subtotal"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        izquierda.addWidget(QLabel("🧾 Productos agregados"))
        izquierda.addWidget(self.tabla)

        self.lbl_total = QLabel("Total: $0.00")
        izquierda.addWidget(self.lbl_total)

        main_layout.addLayout(izquierda, 3)

        # 🎛️ Derecha: acciones
        acciones = QVBoxLayout()

        self.btn_escanear = QPushButton("📷 Iniciar escaneo")
        self.btn_escanear.setCheckable(True)
        self.btn_escanear.clicked.connect(self.toggle_escaneo)
        acciones.addWidget(self.btn_escanear)

        btn_manual = QPushButton("📥 Ingreso manual")
        btn_manual.clicked.connect(self.ingreso_manual)
        acciones.addWidget(btn_manual)

        btn_buscar = QPushButton("🔎 Buscar producto")
        btn_buscar.clicked.connect(self.buscar_producto)
        acciones.addWidget(btn_buscar)

        btn_modificar = QPushButton("✏️ Modificar ítem")
        btn_modificar.clicked.connect(self.modificar_item)
        acciones.addWidget(btn_modificar)

        btn_eliminar = QPushButton("🗑️ Eliminar ítem")
        btn_eliminar.clicked.connect(self.eliminar_item)
        acciones.addWidget(btn_eliminar)

        acciones.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        btn_cancelar = QPushButton("❌ Cancelar venta")
        btn_cancelar.clicked.connect(self.cancelar_venta)
        acciones.addWidget(btn_cancelar)

        self.btn_completar = QPushButton("💰 Completar venta")
        self.btn_completar.clicked.connect(self.confirmar_venta)
        self.btn_completar.setEnabled(False)
        acciones.addWidget(self.btn_completar)

        wrapper = QWidget()
        wrapper.setLayout(acciones)
        main_layout.addWidget(wrapper, 1)

        # Iniciar escaneo automáticamente solo al abrir la venta
        self.btn_escanear.setChecked(True)
        self.toggle_escaneo()

    def toggle_escaneo(self):
        if self.btn_escanear.isChecked():
            self.btn_escanear.setText("⏹️ Detener escaneo")
            self.camara_loop = CamaraLoopThread()
            self.camara_loop.codigo_leido.connect(self.codigo_detectado)
            self.camara_loop.frame_listo.connect(self.mostrar_frame_camara)
            self.camara_loop.start()
            self.lbl_preview.setText("")  # Limpia el texto
            # self.lbl_preview.setPixmap(QPixmap())  # Limpia cualquier imagen previa
        else:
            self.detener_escaneo()

    def codigo_detectado(self, codigo: str):
        # Desactivar escaneo temporalmente

        resultado = self.agregar_por_codigo(codigo)

        if resultado:
            self.camara_loop._pausado = True
            # Reproducir sonido de beep
            self.beep.play()
            # self.actualizar_estado_completar()

            # Reactivar escaneo inmediatamente
            QTimer.singleShot(1000, lambda: setattr(self.camara_loop, "_pausado", False))

    def agregar_por_codigo(self, codigo: str, cantidad: int = 1, interactivo: bool = False) -> bool:
        p = productos.obtener_producto_por_codigo(codigo)
        if not p:
            return False

        # Si interactivo → preguntar por la cantidad
        if interactivo:
            cantidad_ingresada = solicitar_cantidad(
                parent=self,
                descripcion=p["descripcion"],
                stock=p["stock"]
            )
            if cantidad_ingresada is None:
                return True  # Usuario canceló sin error
            cantidad = cantidad_ingresada

        if cantidad > p["stock"]:
            QMessageBox.warning(
                self, "Stock insuficiente",
                f"Stock disponible: {p['stock']}.\nIntentaste agregar {cantidad} unidad(es)."
            )
            return True
            
        # Revisar si ya está en el carrito
        for item in self.carrito:
            if item["codigo"] == codigo:
                total_cantidad = item["cantidad"] + cantidad
                if total_cantidad > p["stock"]:
                    QMessageBox.warning(
                        self, "Stock insuficiente",
                        f"Ya tenés {item['cantidad']} en el carrito.\nStock disponible: {p['stock']}."
                    )
                    return True
                item["cantidad"] = total_cantidad
                # self.actualizar_estado_completar()
                self.refrescar_tabla()
                return True

        # Nuevo producto
        nuevo = {
            "nombre": p["nombre"],
            "codigo": p["codigo_barra"],
            "descripcion": p["descripcion"],
            "precio_unitario": p["precio_venta"],
            "cantidad": cantidad,
            "stock": p["stock"],
            "precio_compra": p["precio_compra"]
        }
        self.carrito.append(nuevo)
        self.refrescar_tabla()
        return True

    def refrescar_tabla(self):
        self.tabla.setRowCount(len(self.carrito))
        total = 0

        for i, item in enumerate(self.carrito):
            subtotal = item["cantidad"] * item["precio_unitario"]
            total += subtotal

            self.tabla.setItem(i, 0, QTableWidgetItem(item["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(item["cantidad"])))
            self.tabla.setItem(i, 2, QTableWidgetItem(f"${item['precio_unitario']:.2f}"))
            self.tabla.setItem(i, 3, QTableWidgetItem(f"${subtotal:.2f}"))

        self.lbl_total.setText(f"Total: ${total:.2f}")
        self.actualizar_estado_completar()

    def ingreso_manual(self):
        codigo, ok = QInputDialog.getText(self, "Ingreso manual", "📦 Ingresá el código de barras:")
        codigo = codigo.strip()

        if not ok or not codigo:
            return

        # Si el código tiene 13 dígitos y todos son numéricos
        if len(codigo) == 13 and codigo.isdigit():
            codigo = codigo[:12]  # Eliminar dígito de control

        if not self.agregar_por_codigo(codigo, interactivo=True):
            QMessageBox.warning(self, "Código inválido", f"No se encontró el producto con código: {codigo}")


    def buscar_producto(self):
        buscador = BuscarProductoDialog(self.sesion, modo="seleccionar")
        if buscador.exec():
            resultado = buscador.obtener_codigo_seleccionado()
            if resultado:
                if isinstance(resultado, tuple):
                    codigo, cantidad = resultado
                else:
                    codigo, cantidad = resultado, 1  # fallback por compatibilidad
                self.agregar_por_codigo(codigo, cantidad)
                # self.actualizar_estado_completar()

    def modificar_item(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Nada seleccionado", "Seleccioná un ítem del carrito para modificar.")
            return

        item = self.carrito[fila]
        codigo = item["codigo"]
        nombre = item["nombre"]
        cantidad_actual = item["cantidad"]

        # 🧾 Obtener stock actual desde base
        producto = productos.obtener_producto_por_codigo(codigo)
        if not producto:
            QMessageBox.critical(self, "Error", "No se pudo obtener el producto.")
            return

        stock_disponible = producto["stock"]
        if stock_disponible < 1:
            QMessageBox.warning(self, "Sin stock", "Este producto ya no tiene stock.")
            return

        nueva_cant, ok = QInputDialog.getInt(
            self,
            "Modificar cantidad",
            f"{nombre}\nStock disponible: {stock_disponible}\nCantidad actual: {cantidad_actual}\nNueva cantidad:",
            cantidad_actual,      # valor predeterminado
            1,                    # mínimo
            stock_disponible      # máximo
        )

        if ok:
            item["cantidad"] = nueva_cant
            self.refrescar_tabla()
            # self.actualizar_estado_completar()

    def eliminar_item(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Nada seleccionado", "Seleccioná un ítem del carrito para eliminar.")
            return

        producto = self.carrito[fila]
        nombre = producto["nombre"]

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar {nombre} del carrito?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.carrito.pop(fila)
            # self.actualizar_estado_completar()
            self.refrescar_tabla()

    def cancelar_venta(self):
        if not self.carrito:
            self.reject()
            return
        confirm = QMessageBox.question(
            self,
            "Cancelar venta",
            "⚠️ Se perderán todos los productos cargados en esta venta.\n¿Querés salir?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.actualizar_estado_completar()
            self.reject()

    def confirmar_venta(self):
        if not self.carrito:
            QMessageBox.warning(self, "Carrito vacío", "⚠️ No hay productos en la venta.")
            return

        
        # 🚨 Verificación previa de stock real por cada producto
        for item in self.carrito:
            producto = productos.obtener_producto_por_codigo(item["codigo"])
            if not producto:
                QMessageBox.critical(self, "Error", f"No se pudo obtener el producto {item['codigo']}.")
                return

            if item["cantidad"] > producto["stock"]:
                QMessageBox.warning(
                    self,
                    "Stock insuficiente",
                    f"🛑 El producto '{producto['nombre']}' solo tiene {producto['stock']} unidades disponibles."
                )
                return

            # ⚠️ Advertencia si baja de stock mínimo
            stock_final = producto["stock"] - item["cantidad"]
            if stock_final < producto.get("stock_minimo", 0):
                QMessageBox.information(
                    self,
                    "Stock bajo",
                    f"🔔 El stock de '{producto['nombre']}' quedará por debajo del mínimo ({producto['stock_minimo']})."
                )

        # 💳 Seleccionar método de pago
        metodo, ok = QInputDialog.getItem(
            self,
            "Método de pago",
            "Seleccioná el método de pago:",
            ["Efectivo", "Tarjeta", "Transferencia"],
            0,
            False
        )
        if not ok:
            return

        exito = registrar_venta(self.sesion, self.carrito, metodo)

        if exito:
            QMessageBox.information(self, "Éxito", "✅ Venta registrada correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar la venta.")

    def mostrar_frame_camara(self, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.lbl_preview.setPixmap(pixmap.scaled(
            self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.btn_escanear.isChecked():
            self.detener_escaneo()
        else:
            super().keyPressEvent(event)


    def detener_escaneo(self):
        self.btn_escanear.setChecked(False)
        self.btn_escanear.setText("📷 Iniciar escaneo")

        if self.camara_loop:
            try:
                self.camara_loop.frame_listo.disconnect(self.mostrar_frame_camara)
            except TypeError:
                pass  # ya estaba desconectado

            self.camara_loop.detener()
            self.camara_loop.wait()
            self.camara_loop = None

        self.lbl_preview.setPixmap(QPixmap())  # Limpia imagen congelada
        self.lbl_preview.setText("Cámara desactivada")
        self.lbl_preview.setAlignment(Qt.AlignCenter)

    
    def actualizar_estado_completar(self):
        self.btn_completar.setEnabled(bool(self.carrito))
