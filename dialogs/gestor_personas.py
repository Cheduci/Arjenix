from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QPushButton, QHBoxLayout, QMessageBox,
    QTableWidgetItem, QLineEdit, QAbstractItemView, QWidget, QLabel, QFileDialog
)
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PySide6.QtGui import QPixmap, QColor
from dialogs.crear_persona import PersonaDialog
from modulos.camara import capturar_foto
from core.personas import *

class GestorPersonasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📇 Gestión de personas")
        self.setMinimumSize(800, 400)
        self.setup_ui()
        self.cargar_personas()
        self.actualizar_estado_botones_foto()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        self.central = QVBoxLayout()

        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar por nombre, apellido, DNI...")
        self.filtro.textChanged.connect(self.aplicar_filtro)
        self.central.addWidget(self.filtro)

        self.tabla = QTableWidget()
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.selectionModel().selectionChanged.connect(self.actualizar_estado_botones_foto)
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

        foto_panel = self.setup_foto_panel()
        main_layout.addWidget(foto_panel)
        self.setLayout(main_layout)

        self.btn_nueva.clicked.connect(self.crear_persona)
        self.btn_editar.clicked.connect(self.editar_persona)
        self.btn_eliminar.clicked.connect(self.eliminar_persona)


# --------------- Inicio Selección de persona
    def seleccion_persona(self):
        fila = self.tabla.currentRow()
        if fila >= 0:
            persona_id, tiene_foto = self.obtener_datos_de_persona_seleccionada()
            self.actualizar_panel_foto(persona_id, tiene_foto)

    def obtener_datos_de_persona_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return None, None
        item_dni = self.tabla.item(fila, 0)
        tiene_foto = self.tabla.item(fila, 5).text() == "✅"
        return item_dni.data(Qt.ItemDataRole.UserRole), tiene_foto

    def actualizar_estado_botones_foto(self):
        persona_id, _ = self.obtener_datos_de_persona_seleccionada()
        habilitado = persona_id is not None
        self.btn_cargar.setEnabled(habilitado)
        self.btn_sacar.setEnabled(habilitado)

# --------------- Fin Selección de persona

# --------------- Inicio panel de foto

    def setup_foto_panel(self):
        panel = QVBoxLayout()
        self.label_foto = QLabel("📷 Sin foto")
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

        self.btn_cargar = QPushButton("📁 Cargar")
        self.btn_cargar.clicked.connect(self.cargar_foto)
        self.btn_sacar = QPushButton("📸 Sacar foto")
        self.btn_sacar.clicked.connect(self.sacar_foto)
        self.btn_eliminar_foto = QPushButton("🗑️ Eliminar")
        self.btn_eliminar_foto.clicked.connect(self.eliminar_foto)
        self.btn_eliminar_foto.setEnabled(False)

        panel.addWidget(self.label_foto)
        panel.addWidget(self.btn_cargar)
        panel.addWidget(self.btn_sacar)
        panel.addWidget(self.btn_eliminar_foto)

        foto_widget = QWidget()
        foto_widget.setLayout(panel)
        return foto_widget
    
    def actualizar_panel_foto(self, persona_id, tiene_foto):
        foto_byte = None
        if tiene_foto:
            foto_byte, error = obtener_foto_persona(persona_id)
            if error:
                QMessageBox.warning(self, "Error", error)
                return
        
            pixmap = QPixmap()
            pixmap.loadFromData(foto_byte)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_foto.setText("")
            self.btn_eliminar_foto.setEnabled(True)
        else:
            self.label_foto.clear()
            self.label_foto.setText("📷 Sin foto")
            self.btn_eliminar_foto.setEnabled(False)
    

    def cargar_foto(self):
        persona_id, tiene_foto = self.obtener_datos_de_persona_seleccionada()
        if persona_id is None:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, "PNG")
            foto_bytes = bytes(buffer.data())
            ok, error = actualizar_foto_persona(persona_id, foto_bytes)
            if ok:
                self.cargar_personas()
                self.actualizar_panel_foto(persona_id, tiene_foto)
                self.btn_eliminar_foto.setEnabled(True)
                QMessageBox.information(self, "Foto actualizada", "✅ Foto actualizada correctamente.")
            else:
                QMessageBox.critical(self, "Error al actualizar foto", f"❌ {error}")

    def sacar_foto(self):
        persona_id, _ = self.obtener_datos_de_persona_seleccionada()
        if persona_id is None:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return
        foto_bytes = capturar_foto()
        if not foto_bytes:
            QMessageBox.warning(self, "Captura cancelada", "No se pudo obtener la foto desde la cámara.")
            return
        ok, error = actualizar_foto_persona(persona_id, foto_bytes)
        if ok:
            tiene_foto = True
            self.cargar_personas()
            self.actualizar_panel_foto(persona_id, tiene_foto)
            self.btn_eliminar_foto.setEnabled(True)
            QMessageBox.information(self, "Foto capturada", "✅ Foto capturada y actualizada correctamente.")
        else:
            QMessageBox.critical(self, "Error al actualizar foto", f"❌ {error}")

    def eliminar_foto(self):
        persona_id, _ = self.obtener_datos_de_persona_seleccionada()
        if persona_id is None:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return
        ok, error = eliminar_foto_persona(persona_id)
        if ok:
            self.label_foto.clear()
            self.label_foto.setText("📷 Sin foto")
            self.btn_eliminar_foto.setEnabled(False)
            self.cargar_personas()
            self.actualizar_panel_foto(persona_id, False)
            QMessageBox.information(self, "Foto eliminada", "✅ Foto eliminada correctamente.")
        else:
            QMessageBox.critical(self, "Error al eliminar foto", f"❌ {error}")

# --------------- Fin panel de foto

# --------------- Inicio gestión de personas
    def cargar_personas(self, personas=None):
        if personas is None:
            self.todas_las_personas = obtener_personas_desde_db()
            personas = self.todas_las_personas
        sin_usuario_ids = {p["id"] for p in obtener_personas_sin_usuario()}
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["DNI", "Nombre", "Apellido", "Email", "Fecha de Nacimiento", "Foto"])
        self.tabla.setRowCount(len(personas))
        for row, persona in enumerate(personas):
            item_dni = QTableWidgetItem(persona["dni"])
            item_dni.setData(Qt.ItemDataRole.UserRole, persona["id"])
            self.tabla.setItem(row, 0, item_dni)
            self.tabla.setItem(row, 1, QTableWidgetItem(persona["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(persona["apellido"]))
            self.tabla.setItem(row, 3, QTableWidgetItem(persona["email"] or ""))
            fecha = persona["fecha_nacimiento"]
            fecha_str = fecha.strftime("%Y-%m-%d") if fecha else ""
            self.tabla.setItem(row, 4, QTableWidgetItem(fecha_str))
            tiene_foto = "✅" if persona["foto"] else "❌"
            self.tabla.setItem(row, 5, QTableWidgetItem(tiene_foto))
            if persona["id"] in sin_usuario_ids:
                for col in range(self.tabla.columnCount()):
                    item = self.tabla.item(row, col)
                    if item:
                        item.setForeground(QColor("gray"))

    def crear_persona(self):
        dialogo = PersonaDialog(modo="crear")
        if dialogo.exec():
            persona = dialogo.obtener_datos()
            persona_id, error = insertar_persona(persona)
            if error is None:
                self.cargar_personas()
                QMessageBox.information(self, "Persona creada", f"✅ {persona['nombre']} {persona['apellido']}, creación exitosa.")
            else:
                QMessageBox.critical(self, "Error al crear persona", f"❌ {error}")

    def editar_persona(self):
        persona_id, _ = self.obtener_datos_de_persona_seleccionada()
        if persona_id is None:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para editar.")
            return
        persona_original = next((p for p in self.todas_las_personas if p["id"] == persona_id), None)
        if not persona_original:
            QMessageBox.critical(self, "Error", "❌ No se pudo encontrar la persona seleccionada.")
            return
        dialogo = PersonaDialog(modo="editar", persona=persona_original)
        dialogo.persona_actualizada.connect(self.on_persona_actualizada)
        dialogo.exec()

    def eliminar_persona(self):
        persona_id, _ = self.obtener_datos_de_persona_seleccionada()
        if persona_id is None:
            QMessageBox.warning(self, "Seleccionar persona", "Por favor, seleccioná una persona para eliminar.")
            return
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
            exito, error = eliminar_persona_por_id(persona_id)
            if exito:
                self.cargar_personas()
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
            self.cargar_personas()
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

# --------------- Fin gestión de personas