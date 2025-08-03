from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
    QPushButton, QHBoxLayout, QMessageBox, QTableWidgetItem, QLineEdit,
    QAbstractItemView)
from core.personas import *
from PySide6.QtCore import Qt
from dialogs.crear_persona import PersonaDialog

class GestorPersonasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📇 Gestión de personas")
        self.setMinimumSize(600, 400)

        self.setup_ui()
        self.cargar_personas()

    def setup_ui(self):
        self.layout_principal = QVBoxLayout()
        self.setLayout(self.layout_principal)

        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar por nombre, apellido, DNI...")
        self.filtro.textChanged.connect(self.aplicar_filtro)
        self.layout_principal.insertWidget(0, self.filtro)

        self.tabla = QTableWidget()
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)      # Selección por fila
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)     # Sólo una fila a la vez

        self.layout_principal.addWidget(self.tabla)

        botones = QHBoxLayout()
        self.btn_nueva = QPushButton("➕ Crear persona")
        self.btn_editar = QPushButton("✏️ Editar seleccionada")
        self.btn_eliminar = QPushButton("🗑️ Eliminar seleccionada")

        botones.addWidget(self.btn_nueva)
        botones.addWidget(self.btn_editar)
        botones.addWidget(self.btn_eliminar)
        self.layout_principal.addLayout(botones)

        self.btn_nueva.clicked.connect(self.crear_persona)
        self.btn_editar.clicked.connect(self.editar_persona)
        self.btn_eliminar.clicked.connect(self.eliminar_persona)


    def cargar_personas(self, personas=None):
        if personas is None:
            self.todas_las_personas = obtener_personas_desde_db()  # Función tuya que hace SELECT
            personas = self.todas_las_personas
        self.tabla.setColumnCount(len(personas[0]) if personas else 0)
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
        if dialogo.exec():
            persona = dialogo.obtener_datos()
            exito, error = actualizar_persona(persona)
            if exito:
                self.cargar_personas()
                QMessageBox.information(self, "Éxito", f"✅ {persona['nombre']} {persona['apellido']} actualizada correctamente.")
            else:
                QMessageBox.critical(self, "Error al editar persona", f"❌ {error}")

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
                QMessageBox.information(self, "Eliminación exitosa", f"✅ {persona['nombre']} {persona['apellido']} fue eliminada correctamente.")
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

