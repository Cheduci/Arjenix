from PySide6.QtCore import QThread, Signal
from modulos.camara import escanear_codigo_opencv
from modulos.camara import leer_codigo_desde_frame
import cv2
from PySide6.QtCore import QElapsedTimer
from PySide6.QtGui import QImage
import numpy as np
from pyzbar.pyzbar import decode
from collections import deque, Counter




class CamaraLoopThread(QThread):
    codigo_leido = Signal(str)
    frame_listo = Signal(QImage)  # <--- Agrega esta línea
    

    def __init__(self):
        super().__init__()
        self._activo = True
        self._pausado = False
        self._ultimo_codigo = ""
        self._cooldown = QElapsedTimer()
        self._historial = deque(maxlen=5)
        

    def detener(self):
        self._activo = False

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara.")
            return

        self._cooldown.start()

        while self._activo:
            if self._pausado:
                QThread.msleep(50)
                continue
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (640, 480))
            codigo = self.procesar_frame(frame)
            
            
            # Emitir frame para preview en Qt
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_listo.emit(qimg)

            if codigo:
                self._historial.append(codigo)

                # Si tenemos suficientes muestras, emitir el más frecuente
                if len(self._historial) == self._historial.maxlen:
                    más_frecuente = Counter(self._historial).most_common(1)[0][0]
                    if más_frecuente != self._ultimo_codigo:
                        if self._cooldown.elapsed() > 200:
                            self.codigo_leido.emit(más_frecuente)
                            self._ultimo_codigo = más_frecuente
                            self._cooldown.restart()

        cap.release()
        # cv2.destroyAllWindows()

    def procesar_frame(self, frame) -> str | None:
        # Dibuja la instrucción sobre el frame
        cv2.putText(frame, "ESC = cancelar escaneo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            puntos = obj.polygon
            hull = cv2.convexHull(np.array(puntos, dtype=np.float32)) if len(puntos) > 4 else puntos
            hull = list(map(tuple, np.squeeze(hull))) if isinstance(hull, np.ndarray) else hull

            cv2.polylines(frame, [np.array(hull, dtype=np.int32)], True, (0, 255, 0), 2)
            x, y = int(hull[0][0]), int(hull[0][1]) - 10
            codigo = obj.data.decode("utf-8")

            if len(codigo) == 13 and codigo.isdigit():
                    codigo = codigo[:12]

            cv2.putText(frame, codigo, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
            return codigo
        
        return None
