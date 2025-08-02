from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QMessageBox, QHBoxLayout, QLineEdit, QLabel, QComboBox
)
from PySide6.QtCore import Qt
from bbdd.db_config import conectar_db
from helpers.validators import validar_email_unico


class GestorUsuariosDialog(QDialog):
    def __init__(self, sesion):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("🛠️ Gestión de usuarios")
        self.setMinimumSize(720, 480)
        self.setLayout(QVBoxLayout())
        self.usuarios = []
        self.fila_actual = None
        self.setup_ui()
        

    def setup_ui(self):
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar usuario...")
        self.input_busqueda.textChanged.connect(self.filtrar_usuarios)
        self.layout().addWidget(self.input_busqueda)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Username", "Nombre", "Apellido", "Rol", "Estado"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.cellClicked.connect(self.cargar_usuario_seleccionado)
        self.tabla.setSortingEnabled(True)
        self.layout().addWidget(self.tabla)

        header = self.tabla.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)


        # 🔄 Formulario inferior para edición
        form = QHBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_apellido = QLineEdit()
        self.input_email = QLineEdit()
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["dueño", "gerente", "repositor","vendedor"])  # Ajustá según tus roles válidos

        self.btn_toggle_activo = QPushButton("🔴 Deshabilitar usuario")
        self.btn_toggle_activo.clicked.connect(self.toggle_estado_usuario)
        self.btn_resetear_password = QPushButton("🔐 Resetear contraseña")
        self.btn_resetear_password.clicked.connect(self.resetear_contrasena_usuario)
        
        
        form.addWidget(QLabel("Nombre"))
        form.addWidget(self.input_nombre)
        form.addWidget(QLabel("Apellido"))
        form.addWidget(self.input_apellido)
        form.addWidget(QLabel("Email"))
        form.addWidget(self.input_email)
        form.addWidget(QLabel("Rol"))
        form.addWidget(self.combo_rol)
        form.addWidget(self.btn_toggle_activo)
        form.addWidget(self.btn_resetear_password)

        self.layout().addLayout(form)

        # 📥 Botones acción
        botones_layout = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar cambios")
        btn_guardar.clicked.connect(self.guardar_cambios)
        botones_layout.addWidget(btn_guardar)
        self.btn_eliminar_usuario = QPushButton("🗑️ Eliminar usuario")
        self.btn_eliminar_usuario.clicked.connect(self.eliminar_usuario_seleccionado)
        botones_layout.addWidget(self.btn_eliminar_usuario)

        self.layout().addLayout(botones_layout)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, p.nombre, p.apellido, r.nombre AS rol, p.email, u.activo
            FROM usuarios u
            JOIN personas p ON u.persona_id = p.id
            LEFT JOIN roles r ON u.rol_id = r.id
            ORDER BY p.apellido, p.nombre;
        """)

        self.usuarios = cur.fetchall()
        conn.close()

        self.tabla.setRowCount(len(self.usuarios))
        for i, (id_, username, nombre, apellido, rol, email, activo) in enumerate(self.usuarios):
            estado = "Activo" if activo else "Deshabilitado"

            self.tabla.setItem(i, 0, QTableWidgetItem(str(id_)))
            self.tabla.setItem(i, 1, QTableWidgetItem(username))
            self.tabla.setItem(i, 2, QTableWidgetItem(nombre))
            self.tabla.setItem(i, 3, QTableWidgetItem(apellido))
            self.tabla.setItem(i, 4, QTableWidgetItem(rol))
            self.tabla.setItem(i, 5, QTableWidgetItem(estado))

            # 🎨 Si está deshabilitado, lo pintamos en gris
            if not activo:
                for j in range(self.tabla.columnCount()):
                    item = self.tabla.item(i, j)
                    if item:
                        item.setForeground(Qt.gray)
                        item.setToolTip("Usuario deshabilitado")

    def cargar_usuario_seleccionado(self, row, column):
        self.fila_actual = row
        _, username, nombre, apellido, rol, email, activo = self.usuarios[row]
        self.input_nombre.setText(nombre)
        self.input_apellido.setText(apellido)
        self.input_email.setText(email or "")
        self.combo_rol.setCurrentText(rol)

        self.actualizar_estado_boton()

        if activo:
            self.btn_toggle_activo.setText("🔴 Deshabilitar usuario")
            self.btn_toggle_activo.setStyleSheet("color: red;")
        else:
            self.btn_toggle_activo.setText("✅ Activar usuario")
            self.btn_toggle_activo.setStyleSheet("color: green;")

    def guardar_cambios(self):
        if self.fila_actual is None:
            QMessageBox.warning(self, "Sin selección", "Debes seleccionar un usuario primero.")
            return

        nombre = self.input_nombre.text().strip()
        apellido = self.input_apellido.text().strip()
        email_nuevo = self.input_email.text().strip()
        rol = self.combo_rol.currentText()

        if not nombre or not apellido:
            QMessageBox.warning(self, "Campos incompletos", "Nombre y apellido son obligatorios.")
            return

        id_usuario = self.usuarios[self.fila_actual][0]

        try:
            conn = conectar_db()
            cur = conn.cursor()

            # 🔍 Obtener email actual desde la DB
            cur.execute("""
                SELECT p.email
                FROM personas p
                JOIN usuarios u ON u.persona_id = p.id
                WHERE u.id = %s
            """, (id_usuario,))
            email_actual = cur.fetchone()[0] if cur.rowcount else ""

            # 📧 Validar email solo si cambió y no está vacío
            if email_nuevo and email_nuevo != email_actual:
                es_valido, mensaje = validar_email_unico(cur, email_nuevo)
                if not es_valido:
                    QMessageBox.warning(self, "Email inválido", mensaje)
                    return

            # 📝 Actualizar datos
            cur.execute("""
                UPDATE personas
                SET nombre = %s, apellido = %s, email = %s
                WHERE id = (SELECT persona_id FROM usuarios WHERE id = %s)
            """, (nombre, apellido, email_nuevo, id_usuario))

            cur.execute("UPDATE usuarios SET rol_id = (SELECT id FROM roles WHERE nombre = %s) WHERE id = %s",
                        (rol, id_usuario))

            conn.commit()
            QMessageBox.information(self, "✅ Guardado", "Los datos del usuario fueron actualizados.")
            self.cargar_usuarios()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Ocurrió un error: {e}")
        finally:
            conn.close()

    def toggle_estado_usuario(self):
        if self.fila_actual is None:
            QMessageBox.warning(self, "Sin selección", "Seleccioná un usuario primero.")
            return

        id_usuario, _, nombre, apellido, rol, _, activo = self.usuarios[self.fila_actual]
        nuevo_estado = not activo
        if rol == "dueño" and activo:
            cantidad_dueños = self.contar_duegnos_activos()
            if cantidad_dueños <= 1:
                QMessageBox.critical(
                    self,
                    "⛔ Acción bloqueada",
                    "No se puede deshabilitar el único usuario con rol de 'dueño'."
                )
                return

        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, id_usuario))
        conn.commit()
        conn.close()

        estado_str = "activado" if nuevo_estado else "deshabilitado"
        QMessageBox.information(
            self,
            "✅ Estado actualizado",
            f"El usuario {nombre} {apellido} fue {estado_str}."
        )

        # 🧩 Refrescar tabla y restaurar selección
        self.cargar_usuarios()

        for fila, usuario in enumerate(self.usuarios):
            if usuario[0] == id_usuario:
                self.tabla.selectRow(fila)
                self.fila_actual = fila
                self.cargar_usuario_seleccionado(fila, 0)
                break


    def actualizar_estado_boton(self):
        if self.fila_actual is None or self.fila_actual >= len(self.usuarios):
            self.btn_toggle_activo.setText("🔴 Deshabilitar usuario")
            return

        usuario = self.usuarios[self.fila_actual]
        activo = usuario[-1]  # suponiendo que 'activo' es el último elemento
        if activo:
            self.btn_toggle_activo.setText("🔴 Deshabilitar usuario")
        else:
            self.btn_toggle_activo.setText("🟢 Activar usuario")

    def filtrar_usuarios(self, texto):
        texto = texto.lower()
        coincidencias = []

        for usuario in self.usuarios:
            id_, username, nombre, apellido, rol, email, activo = usuario
            estado = "activo" if activo else "deshabilitado"  # ← forma textual

            datos = f"{id_} {username} {nombre} {apellido} {rol} {email} {estado}".lower()
            
            if texto.isdigit() and int(texto) == id_:
                coincidencias.append(usuario)
                continue

            if texto in datos:
                coincidencias.append(usuario)

        self.tabla.setRowCount(len(coincidencias))
        for i, (id_, username, nombre, apellido, rol, email, activo) in enumerate(coincidencias):
            estado = "Activo" if activo else "Deshabilitado"

            self.tabla.setItem(i, 0, QTableWidgetItem(str(id_)))
            self.tabla.setItem(i, 1, QTableWidgetItem(username))
            self.tabla.setItem(i, 2, QTableWidgetItem(nombre))
            self.tabla.setItem(i, 3, QTableWidgetItem(apellido))
            self.tabla.setItem(i, 4, QTableWidgetItem(rol))
            self.tabla.setItem(i, 5, QTableWidgetItem(estado))

            if not activo:
                for j in range(self.tabla.columnCount()):
                    item = self.tabla.item(i, j)
                    if item:
                        item.setForeground(Qt.gray)
                        item.setToolTip("Usuario deshabilitado")

    def contar_duegnos_activos(self):
        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
            WHERE r.nombre = 'dueño' AND u.activo = TRUE
        """)
        cantidad = cur.fetchone()[0]
        conn.close()
        return cantidad

    def resetear_contrasena_usuario(self):
        if self.fila_actual is None:
            QMessageBox.warning(self, "Selección requerida", "❗ Seleccioná un usuario primero.")
            return

        id_usuario = self.usuarios[self.fila_actual][0]

        try:
            conn = conectar_db()
            cur = conn.cursor()

            # 🔍 Obtener email actual desde la DB
            cur.execute("""
                SELECT debe_cambiar_password
                FROM usuarios
                WHERE id = %s
            """, (id_usuario,))
            deber_cambiar_password = cur.fetchone()[0] if cur.rowcount else False

            # 📧 Validar email solo si cambió y no está vacío
            if deber_cambiar_password is False:
                cur.execute("""
                    UPDATE usuarios
                    SET debe_cambiar_password = TRUE
                    WHERE id = %s
                """, (id_usuario,))
                conn.commit()
                QMessageBox.information(self, "Contraseña reseteada", "🔐 El usuario deberá cambiar su contraseña al próximo ingreso.")

            else:
                QMessageBox.warning(self, "Contraseña ya reseteada", "🔐 El usuario ya debe cambiar su contraseña.")
                return

            conn.commit()
            self.cargar_usuarios()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Ocurrió un error: {e}")
        finally:
            conn.close()

    def eliminar_usuario_seleccionado(self):
        if self.fila_actual is None:
            QMessageBox.warning(self, "Selección requerida", "❗ Seleccioná un usuario primero.")
            return

        id_usuario = self.usuarios[self.fila_actual][0]
        nombre = self.usuarios[self.fila_actual][2]
        apellido = self.usuarios[self.fila_actual][3]

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar al usuario {nombre} {apellido}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta == QMessageBox.No:
            return

        try:
            conn = conectar_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
            conn.commit()
            QMessageBox.information(self, "Usuario eliminado", f"✅ El usuario {nombre} {apellido} fue eliminado correctamente.")
            self.cargar_usuarios()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Ocurrió un error al eliminar el usuario: {e}")
        finally:
            conn.close()