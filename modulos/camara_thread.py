from PySide6.QtCore import QThread, Signal
from modulos.camara import escanear_codigo_opencv
from modulos.camara import leer_codigo_desde_frame
import cv2
from PySide6.QtCore import QElapsedTimer


class CamaraThread(QThread):
    codigo_detectado = Signal(str)

    def run(self):
        while True:
            codigo = escanear_codigo_opencv()
            if codigo:
                self.codigo_detectado.emit(codigo)

class CamaraLoopThread(QThread):
    codigo_leido = Signal(str)

    def __init__(self):
        super().__init__()
        self._activo = True
        self._ultimo_codigo = ""
        self._cooldown = QElapsedTimer()

    def detener(self):
        self._activo = False

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara.")
            return

        self._cooldown.start()

        while self._activo:
            ret, frame = cap.read()
            if not ret:
                continue

            codigo = leer_codigo_desde_frame(frame)

            if codigo and codigo != self._ultimo_codigo:
                if self._cooldown.elapsed() > 2000:  # mínimo 2s entre lecturas
                    if len(codigo) == 13:
                        codigo = codigo[:12]
                    self.codigo_leido.emit(codigo)
                    self._ultimo_codigo = codigo
                    self._cooldown.restart()

            cv2.putText(frame, "ESC = cancelar escaneo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("📷 Escaneo continuo", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
