from dialogs.buscar_producto import BuscarProductoDialog
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QWidget, QSpacerItem, QSizePolicy,
    QInputDialog, QMessageBox
)
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
from modulos.camara_thread import CamaraThread
from modulos.camara import escanear_codigo_opencv
from core import productos, ventas


class IniciarVentaDialog(QDialog):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("🛒 Iniciar venta")
        self.setMinimumSize(960, 600)
        self.carrito = []

        self.setup_ui()
        self.camara_thread = CamaraThread()
        self.camara_thread.codigo_detectado.connect(self.agregar_por_codigo)
        self.camara_thread.start()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 🧾 Izquierda: productos escaneados
        izquierda = QVBoxLayout()
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

        wrapper = QWidget()
        wrapper.setLayout(acciones)
        main_layout.addWidget(wrapper, 1)

    def iniciar_escaneo(self):
        # ⏳ Podés hacerlo asincrónico luego si lo querés no-bloqueante
        codigo = escanear_codigo_opencv()
        if not codigo:
            return
        self.agregar_por_codigo(codigo)
        self.iniciar_escaneo()  # ⚠️ recursivo simple; puede reemplazarse por loop o hilo

    def iniciar_escaneo_manual(self):
        if hasattr(self, "camara_thread") and self.camara_thread.isRunning():
            return  # Evitamos hilos duplicados

        self.camara_thread = CamaraThread()
        self.camara_thread.codigo_detectado.connect(self.agregar_por_codigo)
        self.camara_thread.finished.connect(self.liberar_thread)
        self.camara_thread.start()

        self.btn_escanear.setEnabled(False)

    def liberar_thread(self):
        self.btn_escanear.setEnabled(True)
        del self.camara_thread  # Limpieza opcional


    def agregar_por_codigo(self, codigo: str):
        p = productos.obtener_producto_por_codigo(codigo)
        if not p:
            return

        # Revisar si ya está en el carrito
        for item in self.carrito:
            if item["codigo"] == codigo:
                if item["cantidad"] >= p["stock"]:
                    QMessageBox.warning(
                        self, "Stock insuficiente",
                        f"No se pueden agregar más unidades.\nStock disponible: {p['stock']}."
                    )
                    return
                item["cantidad"] += 1
                self.refrescar_tabla()
                return

        # Nuevo ítem al carrito
        if p["stock"] < 1:
            QMessageBox.warning(self, "Sin stock", "Este producto no tiene stock disponible.")
            return

        self.carrito.append({
            "codigo": p["codigo_barra"],
            "nombre": p["nombre"],
            "cantidad": 1,
            "precio_unitario": p["precio_venta"]
        })
        self.refrescar_tabla()


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
    
    def ingreso_manual(self):
        codigo, ok = QInputDialog.getText(self, "Ingreso manual", "📦 Ingresá el código de barras:")
        if not ok or not codigo.strip():
            return

        self.agregar_por_codigo(codigo.strip())

    def buscar_producto(self):
        buscador = BuscarProductoDialog(modo="seleccionar")
        buscador.exec()
        codigo = buscador.obtener_codigo_seleccionado()
        
        if codigo:
            self.agregar_por_codigo(codigo)

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
            value=cantidad_actual,
            min=1,
            max=stock_disponible  # ✅ Limita al stock real
        )

        if ok:
            item["cantidad"] = nueva_cant
            self.refrescar_tabla()

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
            self.reject()  # Cierra el diálogo sin marcarlo como aceptado

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

        # 🧾 Registrar venta en base
        from core.ventas import registrar_venta
        exito = registrar_venta(self.sesion["usuario"], self.carrito, metodo)

        if exito:
            QMessageBox.information(self, "Éxito", "✅ Venta registrada correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar la venta.")

    def toggle_escaneo(self):
        if self.btn_escanear.isChecked():
            self.btn_escanear.setText("⏹️ Detener escaneo")
            from modulos.camara_thread import CamaraLoopThread
            self.camara_loop = CamaraLoopThread()
            self.camara_loop.codigo_leido.connect(self.codigo_detectado)
            self.camara_loop.start()
        else:
            self.btn_escanear.setText("📷 Iniciar escaneo")
            if hasattr(self, "camara_loop"):
                self.camara_loop.detener()
                self.camara_loop.wait()

    def codigo_detectado(self, codigo: str):

        sonido = QSoundEffect()
        sonido.setSource(QUrl.fromLocalFile("sonidos/beep.mp3"))
        sonido.setVolume(0.4)
        sonido.play()

        self.agregar_por_codigo(codigo)
