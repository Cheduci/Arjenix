from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QAbstractItemView, QInputDialog, QHBoxLayout
from core.productos import crear_categoria, listar_categorias, eliminar_categoria, renombrar_categoria, categoria_en_uso

class GestionarCategoriasDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🗂️ Categorías del sistema")
        self.resize(400, 300)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.layout = QVBoxLayout()

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(1)
        self.tabla.setHorizontalHeaderLabels(["Nombre"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.tabla)

        # 🧱 Botones: Agregar / Editar / Eliminar
        hbox_botones = QHBoxLayout()

        btn_agregar = QPushButton("➕ Agregar")
        btn_agregar.clicked.connect(self.agregar_categoria)
        hbox_botones.addWidget(btn_agregar)

        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_categoria)
        hbox_botones.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_categoria)
        hbox_botones.addWidget(self.btn_eliminar)

        self.layout.addLayout(hbox_botones)

        self.setLayout(self.layout)

        self.tabla.itemSelectionChanged.connect(self.actualizar_botones)
        self.actualizar_botones()

    def cargar_datos(self):
        categorias = listar_categorias()
        self.tabla.setRowCount(len(categorias))
        for i, nombre in enumerate(categorias):
            self.tabla.setItem(i, 0, QTableWidgetItem(nombre))

    def actualizar_botones(self):
        tiene_seleccion = self.tabla.currentRow() != -1
        self.btn_editar.setEnabled(tiene_seleccion)
        self.btn_eliminar.setEnabled(tiene_seleccion)


    def agregar_categoria(self):
        nombre, ok = QInputDialog.getText(self, "Agregar categoría", "Nombre de la nueva categoría:")
        if ok and nombre.strip():
            try:
                crear_categoria(nombre.strip())
                self.cargar_datos()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo crear la categoría:\n{e}")

    def editar_categoria(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Sin selección", "Seleccioná una categoría para editar.")
            return

        nombre_actual = self.tabla.item(fila, 0).text()

        nuevo_nombre, ok = QInputDialog.getText(self, "Editar categoría", "Nuevo nombre:", text=nombre_actual)
        if ok and nuevo_nombre.strip() and nuevo_nombre.strip() != nombre_actual:
            try:
                from core.productos import renombrar_categoria
                renombrar_categoria(nombre_actual, nuevo_nombre.strip())
                self.cargar_datos()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo editar la categoría:\n{e}")


    def eliminar_categoria(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return

        nombre = self.tabla.item(fila, 0).text()

        if categoria_en_uso(nombre):
            QMessageBox.information(self, "No se puede eliminar", f"La categoría “{nombre}” está en uso por al menos un producto.")
            return

        confirmacion = QMessageBox.question(self, "Confirmar", f"¿Eliminar la categoría “{nombre}”?")
        if confirmacion == QMessageBox.Yes:
            if eliminar_categoria(nombre):
                self.cargar_datos()

