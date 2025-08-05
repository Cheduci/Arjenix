from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
    QPushButton, QHBoxLayout, QMessageBox, QTableWidgetItem, QLineEdit,
    QAbstractItemView, QWidget, QLabel, QFileDialog)
from core.personas import *
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PySide6.QtGui import QPixmap
from dialogs.crear_persona import PersonaDialog
from modulos.camara import capturar_foto

class GestorPersonasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📇 Gestión de personas")
        self.setMinimumSize(800, 400)

        self.setup_ui()
        self.cargar_personas()

    def setup_ui(self):
        main_layout = QHBoxLayout()

        self.central = QVBoxLayout()
        # self.setLayout(self.layout_principal)

        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar por nombre, apellido, DNI...")
        self.filtro.textChanged.connect(self.aplicar_filtro)
        self.central.insertWidget(0, self.filtro)

        self.tabla = QTableWidget()
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)      # Selección por fila
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)     # Sólo una fila a la vez
        self.tabla.itemSelectionChanged.connect(self.seleccion_persona)

        self.central.addWidget(self.tabla)

        botones = QHBoxLayout()
        self.btn_nueva = QPushButton("➕ Crear persona")
        self.btn_editar = QPushButton("✏️ Editar seleccionada")
        self.btn_eliminar = QPushButton("🗑️ Eliminar seleccionada")

        botones.addWidget(self.btn_nueva)
        botones.addWidget(self.btn_editar)
        botones.addWidget(self.btn_eliminar)
        self.central.addLayout(botones)

        contenedor_central = QWidget()
        contenedor_central.setLayout(self.central)
        main_layout.addWidget(contenedor_central)

        panel_foto = self.setup_foto_panel()
        foto_widget = QWidget()
        foto_widget.setLayout(panel_foto)
        main_layout.addWidget(foto_widget)
        
        self.setLayout(main_layout)

        self.btn_nueva.clicked.connect(self.crear_persona)
        self.btn_editar.clicked.connect(self.editar_persona)
        self.btn_eliminar.clicked.connect(self.eliminar_persona)

    def setup_foto_panel(self):
        panel = QVBoxLayout()

        self.label_foto = QLabel()
        self.label_foto.setFixedSize(128, 128)
        self.label_foto.setAlignment(Qt.AlignCenter)
        self.label_foto.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f8f8f8;
                font-size: 12pt;
                color: #666;
            }
        """)

        self.label_foto.setText("📷 Sin foto")

        btn_cargar = QPushButton("📁 Cargar")
        btn_cargar.clicked.connect(self.cargar_foto)

        btn_sacar = QPushButton("📸 Sacar foto")
        btn_sacar.clicked.connect(self.sacar_foto)

        self.btn_eliminar_foto = QPushButton("🗑️ Eliminar")
        self.btn_eliminar_foto.clicked.connect(self.eliminar_foto)
        self.btn_eliminar_foto.setEnabled(False)

        panel = QVBoxLayout()
        panel.addWidget(btn_cargar)
        panel.addWidget(btn_sacar)
        panel.addWidget(self.btn_eliminar_foto)

        contenedor = QVBoxLayout()
        contenedor.addWidget(self.label_foto)
        contenedor.addLayout(panel)

        return contenedor

    def actualizar_panel_foto(self, persona):
        foto_data = persona.get("foto")
        if foto_data is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(foto_data)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_foto.setText("")  # Limpia el texto
            self.btn_eliminar_foto.setEnabled(True)
        else:
            self.label_foto.clear()
            self.label_foto.setText("📷 Sin foto")
            self.btn_eliminar_foto.setEnabled(False)

    def seleccion_persona(self):
        fila = self.tabla.currentRow()
        if fila >= 0:
            persona = self.obtener_datos_de_persona(fila)  # Implementa este método según tu lógica
            self.actualizar_panel_foto(persona)

    def obtener_datos_de_persona(self, fila: int) -> dict:
        dni = self.tabla.item(fila, 0).text()
        nombre = self.tabla.item(fila, 1).text()
        apellido = self.tabla.item(fila, 2).text()
        tiene_foto = self.tabla.item(fila, 5).text() == "✅"

        foto_byte = None
        if tiene_foto:
            foto_byte, error = obtener_foto_persona(dni)
            if error:
                QMessageBox.warning(self, "Error", error)
                return {}

        return {
            "nombre": nombre,
            "apellido": apellido,
            "dni": dni,
            "foto": foto_byte if tiene_foto else None,
        }


    def cargar_foto(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return

        # Recuperamos el ID oculto en la columna 0 (DNI)
        item_dni = self.tabla.item(fila, 0)
        persona_id = item_dni.data(Qt.ItemDataRole.UserRole)

        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # 🔁 Convertir el pixmap en bytes usando QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, "PNG")  # También puede ser "JPG", pero PNG preserva transparencia
            foto_bytes = bytes(buffer.data())

            # 💾 Guardar en el diccionario de la persona
            ok, error = actualizar_foto_persona(persona_id, foto_bytes)

            if ok:
                self.cargar_personas()  # Refresca la tabla
                self.actualizar_panel_foto(self.obtener_datos_de_persona(self.tabla.currentRow()))
                QMessageBox.information(self, "Foto actualizada", "✅ Foto actualizada correctamente.")
            else:
                QMessageBox.critical(self, "Error al actualizar foto", f"❌ {error}")

    def sacar_foto(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return

        # Recuperamos el ID oculto en la columna 0 (DNI)
        item_dni = self.tabla.item(fila, 0)
        persona_id = item_dni.data(Qt.ItemDataRole.UserRole)

        foto_bytes = capturar_foto()
        if not foto_bytes:
            QMessageBox.warning(self, "Captura cancelada", "No se pudo obtener la foto desde la cámara.")
            return

        ok, error = actualizar_foto_persona(persona_id, foto_bytes)
        if not ok:
            QMessageBox.critical(self, "Error al actualizar foto", f"❌ {error}")
            return
        QMessageBox.information(self, "Foto capturada", "✅ Foto capturada y actualizada correctamente.")
        
        self.cargar_personas()  # Refresca la tabla
        self.actualizar_panel_foto(self.obtener_datos_de_persona(fila))

        self.btn_eliminar_foto.setEnabled(True)

    def eliminar_foto(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return

        # Recuperamos el ID oculto en la columna 0 (DNI)
        item_dni = self.tabla.item(fila, 0)
        persona_id = item_dni.data(Qt.ItemDataRole.UserRole)

        if not persona_id:
            QMessageBox.warning(self, "Advertencia", "No se pudo obtener el ID de la persona")
            return

        ok, error = eliminar_foto_persona(persona_id)

        if ok:
            self.label_foto.clear()
            self.label_foto.setText("📷 Sin foto")
            self.btn_eliminar_foto.setEnabled(False)
            self.cargar_personas()  # Refresca la tabla
            if hasattr(self, "persona"):
                self.persona["foto"] = None
            QMessageBox.information(self, "Foto eliminada", "✅ Foto eliminada correctamente.")
        else:
            QMessageBox.critical(self, "Error al eliminar foto", f"❌ {error}")
    
    def cargar_personas(self, personas=None):
        if personas is None:
            self.todas_las_personas = obtener_personas_desde_db()  # Función tuya que hace SELECT
            personas = self.todas_las_personas
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["DNI", "Nombre", "Apellido", "Email", "Fecha de Nacimiento", "Foto"])
        self.tabla.setRowCount(len(personas))

        for row, persona in enumerate(personas):
            item_dni = QTableWidgetItem(persona["dni"])
            item_dni.setData(Qt.ItemDataRole.UserRole, persona["id"])  # Guardás el ID real
            self.tabla.setItem(row, 0, item_dni)
            self.tabla.setItem(row, 1, QTableWidgetItem(persona["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(persona["apellido"]))
            self.tabla.setItem(row, 3, QTableWidgetItem(persona["email"] or ""))
            fecha = persona["fecha_nacimiento"]
            fecha_str = fecha.strftime("%Y-%m-%d") if fecha else ""
            self.tabla.setItem(row, 4, QTableWidgetItem(fecha_str))

            tiene_foto = "✅" if persona["foto"] else "❌"
            self.tabla.setItem(row, 5, QTableWidgetItem(tiene_foto))

    def crear_persona(self):
        dialogo = PersonaDialog(modo="crear")
        if dialogo.exec():
            persona = dialogo.obtener_datos()
            persona_id, error = insertar_persona(persona)
            if error is None:
                self.persona_id = persona_id
                self.cargar_personas()
            else:
                QMessageBox.critical(self, "Error al crear persona", f"❌ {error}")

    def editar_persona(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return

        # Recuperamos el ID oculto en la columna 0 (DNI)
        item_dni = self.tabla.item(fila, 0)
        persona_id = item_dni.data(Qt.ItemDataRole.UserRole)

        # Buscamos la persona por ID en la lista original
        persona_original = next((p for p in self.todas_las_personas if p["id"] == persona_id), None)
        if not persona_original:
            QMessageBox.critical(self, "Error", "❌ No se pudo encontrar la persona seleccionada.")
            return

        dialogo = PersonaDialog(modo="editar", persona=persona_original)
        dialogo.persona_actualizada.connect(self.on_persona_actualizada)
        dialogo.exec()  # no necesitas hacer nada más acá; la señal se encarga

    def eliminar_persona(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para eliminar.")
            return

        item_dni = self.tabla.item(fila, 0)
        persona_id = item_dni.data(Qt.ItemDataRole.UserRole)
        persona = next((p for p in self.todas_las_personas if p["id"] == persona_id), None)

        if not persona:
            QMessageBox.critical(self, "Error", "❌ No se pudo recuperar la persona seleccionada.")
            return

        confirmar = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar a {persona['nombre']} {persona['apellido']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar == QMessageBox.Yes:
            exito,error = eliminar_persona_por_id(persona_id)
            if exito:
                self.cargar_personas()
                # self.persona_eliminada.emit(persona_id)  # Señal opcional
                QMessageBox.information(self, "Eliminación exitosa", f"✅ {persona['nombre']} {persona['apellido']}, eliminación exitosa.")
            else:
                QMessageBox.critical(self, "Error al eliminar persona", f"❌ {error}")
        

    def aplicar_filtro(self, texto):
        texto = texto.lower()
        filtradas = [
            p for p in self.todas_las_personas
            if texto in p["nombre"].lower()
            or texto in p["apellido"].lower()
            or texto in str(p["dni"]).lower()
            or texto in str(p["email"] or "").lower()
        ]
        self.cargar_personas(filtradas)

    def on_persona_actualizada(self, datos_persona: dict):
        exito, error = actualizar_persona(datos_persona)
        if exito:
            self.cargar_personas()  # 🔁 Refresca la tabla
            QMessageBox.information(
                self,
                "Persona actualizada",
                f"✅ {datos_persona['nombre']} {datos_persona['apellido']}, actualización exitosa."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"⚠️ No se pudo actualizar a {datos_persona['nombre']} {datos_persona['apellido']}: {error}"
            )
