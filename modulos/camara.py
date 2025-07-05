import cv2
import numpy as np
from pyzbar.pyzbar import decode

def escanear_codigo_opencv():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        return None

    print("📷 Escaneando... Presione ESC para cancelar.")
    codigo_detectado = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Error al capturar imagen.")
            break

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            puntos = obj.polygon
            if len(puntos) > 4:
                hull = cv2.convexHull(np.array([p for p in puntos], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = puntos

            cv2.polylines(frame, [np.array(hull, dtype=np.int32)], True, (0, 255, 0), 2)
            x = int(hull[0][0])
            y = int(hull[0][1]) - 10
            codigo = obj.data.decode("utf-8")
            cv2.putText(frame, codigo, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
            codigo_detectado = codigo

        cv2.imshow("Escaneo de código", frame)
        key = cv2.waitKey(1) & 0xFF

        if codigo_detectado:
            if len(codigo_detectado) == 13:
                codigo_detectado = codigo_detectado[:12]
            print(f"✅ Código detectado: {codigo_detectado}")
            break

        if key == 27:
            print("🚫 Escaneo cancelado.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return codigo_detectado

def obtener_codigo_barra():
    codigo = escanear_codigo_opencv()
    if not codigo:
        eleccion = input("❓ ¿Ingresar código manualmente? (s/n): ").strip().lower()
        if eleccion == "s":
            codigo = input("🔢 Ingrese código de barras: ").strip()
    return codigo

def capturar_foto() -> bytes | None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error al abrir la cámara.")
        return None

    print("📸 Presione ESPACIO para capturar o ESC para cancelar.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error al capturar la imagen.")
            break

        cv2.imshow("Vista previa - Cámara", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # ESPACIO
            cap.release()
            cv2.destroyAllWindows()

            # Convertir a JPEG en memoria
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                print("❌ Error al codificar la imagen.")
                return None

            print("✅ Foto capturada y codificada.")
            return buffer.tobytes()

        elif key == 27:  # ESC
            print("🚫 Captura cancelada.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None