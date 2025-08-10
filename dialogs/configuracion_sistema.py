from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton, QPushButton, QLabel,
                                   QHBoxLayout, QMessageBox)
from PySide6.QtCore import Signal
from core.configuracion import guardar_configuracion_sistema, obtener_configuracion_sistema, config_signals

class ConfiguracionSistemaDialog(QDialog):
    # configuracion_actualizada = Signal(dict)  # Emitir cambios si querés actualizar la sesión

    def __init__(self, sesion, config_sistema, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración de sistema")
        self.setMinimumWidth(400)
        self.sesion = sesion
        self.config_sistema = config_sistema
        self.setup_ui()
        self.cargar_configuraciones()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # 🧭 Sección: Modo de código de barras
        self.group_codigo = QGroupBox("Modo de código de barra")
        self.radio_auto = QRadioButton("🔄 Generar automáticamente")
        self.radio_manual = QRadioButton("⌨️ Ingresar manualmente")
        self.radio_mixto = QRadioButton("⚙️ Modo mixto")

        codigo_layout = QVBoxLayout()
        codigo_layout.addWidget(self.radio_auto)
        codigo_layout.addWidget(self.radio_manual)
        codigo_layout.addWidget(self.radio_mixto)
        self.group_codigo.setLayout(codigo_layout)

        # 📦 Placeholder para futuras configuraciones
        self.group_otros = QGroupBox("Otras configuraciones (próximamente)")
        otros_layout = QVBoxLayout()
        otros_layout.addWidget(QLabel("🧪 Aquí podrás elegir temas, idioma, etc."))
        self.group_otros.setLayout(otros_layout)

        # ✅ Botones
        self.btn_guardar = QPushButton("💾 Guardar preferencias")
        self.btn_cancelar = QPushButton("❌ Cancelar")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)

        # 📐 Ensamblar todo
        self.layout.addWidget(self.group_codigo)
        self.layout.addWidget(self.group_otros)
        self.layout.addLayout(btn_layout)

        # 🔗 Conexiones
        self.btn_guardar.clicked.connect(self.guardar_configuraciones)
        self.btn_cancelar.clicked.connect(self.reject)

    def cargar_configuraciones(self):
        # Modo de código de barra
        modo = self.config_sistema.get("modo_codigo_barra", "mixto")
        if modo == "auto":
            self.radio_auto.setChecked(True)
        elif modo == "manual":
            self.radio_manual.setChecked(True)
        else:
            self.radio_mixto.setChecked(True)

    def guardar_configuraciones(self):
        # Modo de codigo de barra
        if self.radio_auto.isChecked():
            modo = "auto"
        elif self.radio_manual.isChecked():
            modo = "manual"
        else:
            modo = "mixto"
        self.config_sistema["modo_codigo_barra"] = modo

        # 🔄 Actualizar sesión y emitir señal
        guardar_configuracion_sistema(self.config_sistema)
        config_signals.configuracion_actualizada.emit()
        self.config_sistema = obtener_configuracion_sistema()

        QMessageBox.information(self, "Configuración guardada", "✅ Tus configuraciones fueron actualizadas.")
        self.accept()
