import bcrypt
from datetime import datetime
import random
import string
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

def exportar_pdf(username, password_temporal):
    # Generar PDF con credenciales
    ruta_pdf = f"credenciales_{username}.pdf"
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4
    y = alto - 4 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Credenciales de acceso")
    y -= 1.5 * cm

    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, f"Usuario: {username}")
    y -= 1 * cm
    c.drawString(2 * cm, y, f"Contraseña temporal: {password_temporal}")
    y -= 1 * cm
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(2 * cm, y, "Se solicitará cambiar la contraseña al primer ingreso.")

    c.save()
    print(f"📄 PDF generado: {os.path.abspath(ruta_pdf)}")


def generar_password_temporal(longitud=8):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(caracteres, k=longitud))

def crear_usuario(cur):
    print("\n👤 Crear nuevo usuario del sistema")

    # Mostrar personas disponibles (sin usuario creado aún)
    cur.execute("""
        SELECT p.id, p.dni, p.nombre, p.apellido
        FROM personas p
        LEFT JOIN usuarios u ON p.id = u.persona_id
        WHERE u.id IS NULL AND p.activo = TRUE
        ORDER BY p.apellido, p.nombre;
    """)
    personas = cur.fetchall()

    if not personas:
        print("⚠️ No hay personas sin usuario.")
        op = input("¿Deseás registrar una nueva? [S/n]: ").strip().lower()
        if op in ("s", "si", ""):
            crear_persona(cur)
            return crear_usuario(cur)  # vuelve a intentarlo luego de crear
        return

    print("\nPersonas disponibles:")
    for pid, dni, nom, ape in personas:
        print(f"[{pid}] {ape.upper()}, {nom} (DNI: {dni})")

    try:
        persona_id = int(input("\nID de persona: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if persona_id not in [p[0] for p in personas]:
        print("❌ ID no válido.")
        return

    # 🧩 Generar sugerencia automática
    nombre_base = nom.lower().strip()
    apellido_base = ape.lower().split()[0]
    sugerido = f"{nombre_base[0]}{apellido_base}"

    # Intentar evitar colisión
    sugerido_base = sugerido
    contador = 1

    cur.execute("SELECT 1 FROM usuarios WHERE username = %s;", (sugerido,))
    while cur.fetchone():
        sugerido = f"{sugerido_base}{contador}"
        contador += 1
        cur.execute("SELECT 1 FROM usuarios WHERE username = %s;", (sugerido,))

    print(f"\n✨ Sugerencia: podés usar '{sugerido}' como nombre de usuario.")

    usar = input(f"¿Querés usar '{sugerido}' como username? [S/n]: ").strip().lower()
    if usar in ("s", "si", ""):
        username = sugerido
    else:
        # Loop hasta obtener uno válido
        while True:
            username = input("Escribí un nombre de usuario: ").strip()
            if not username:
                print("❌ No puede estar vacío.")
                continue
            cur.execute("SELECT 1 FROM usuarios WHERE username = %s;", (username,))
            if cur.fetchone():
                print("⚠️ Ya existe. Probá otro.")
            else:
                break

    # Mostrar roles disponibles
    cur.execute("SELECT id, nombre FROM roles ORDER BY id;")
    roles = cur.fetchall()

    print("\nRoles disponibles:")
    for rid, nombre in roles:
        print(f"[{rid}] {nombre}")

    try:
        rol_id = int(input("ID del rol a asignar: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if rol_id not in [r[0] for r in roles]:
        print("❌ Rol no válido.")
        return

    password_temporal = generar_password_temporal()
    hash_pw = bcrypt.hashpw(password_temporal.encode(), bcrypt.gensalt()).decode()

    try:
        cur.execute("""
            INSERT INTO usuarios (persona_id, username, password_hash, rol_id, debe_cambiar_password, activo)
            VALUES (%s, %s, %s, %s, TRUE, TRUE);
        """, (persona_id, username, hash_pw, rol_id))
        cur.connection.commit()
        print(f"\n✅ Usuario creado con éxito.")
        print(f"🔑 Contraseña temporal: {password_temporal}")
        print("🔁 Se solicitará cambiarla en el primer inicio de sesión.")

        exportar_pdf(username, password_temporal)
    except Exception as e:
        cur.connection.rollback()
        print(f"❌ Error al crear usuario: {e}")

def activar_inactivar_usuario(cur):
    print("\n🔄 Activar / Inactivar usuario")

    # Mostrar todos los usuarios con estado actual
    cur.execute("""
        SELECT u.id, u.username, p.nombre, p.apellido, u.activo
        FROM usuarios u
        JOIN personas p ON u.persona_id = p.id
        ORDER BY u.activo DESC, p.apellido;
    """)
    usuarios = cur.fetchall()

    if not usuarios:
        print("⚠️ No hay usuarios registrados.")
        return

    print("\nID | Usuario      | Nombre completo         | Estado")
    print("------------------------------------------------------")
    for uid, user, nom, ape, activo in usuarios:
        estado = "✅ Activo" if activo else "🚫 Inactivo"
        print(f"{uid:<3} {user:<13} {ape.upper()}, {nom:<15} {estado}")

    try:
        id_modificar = int(input("\nID del usuario que querés modificar: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if id_modificar not in [u[0] for u in usuarios]:
        print("❌ No se encontró ese usuario.")
        return

    # Consultar estado actual
    cur.execute("SELECT activo FROM usuarios WHERE id = %s;", (id_modificar,))
    activo_actual = cur.fetchone()[0]

    nuevo_estado = not activo_actual
    cur.execute("UPDATE usuarios SET activo = %s WHERE id = %s;", (nuevo_estado, id_modificar))
    cur.connection.commit()

    estado_nuevo = "activado ✅" if nuevo_estado else "inactivado 🚫"
    print(f"\n🗂️ Usuario {estado_nuevo} con éxito.")


def cambiar_contrasena_usuario(cur):
    print("\n🔐 Resetear contraseña de usuario")

    # Mostrar lista de usuarios activos
    cur.execute("""
        SELECT u.id, u.username, p.nombre, p.apellido
        FROM usuarios u
        JOIN personas p ON u.persona_id = p.id
        ORDER BY p.apellido, p.nombre;
    """)
    usuarios = cur.fetchall()

    if not usuarios:
        print("⚠️ No hay usuarios registrados.")
        return

    print("\nID | Usuario      | Nombre completo")
    print("----------------------------------------")
    for uid, username, nombre, apellido in usuarios:
        print(f"{uid:<3} {username:<13} {apellido.upper()}, {nombre}")

    try:
        id_usuario = int(input("\nID del usuario a modificar: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if id_usuario not in [u[0] for u in usuarios]:
        print("❌ Usuario no encontrado.")
        return

    password_nueva = generar_password_temporal()
    hash_pw = bcrypt.hashpw(password_nueva.encode(), bcrypt.gensalt()).decode()

    cur.execute("""
        UPDATE usuarios
        SET password_hash = %s,
            debe_cambiar_password = TRUE
        WHERE id = %s;
    """, (hash_pw, id_usuario))
    cur.connection.commit()

    print(f"\n🔄 Contraseña reseteada con éxito.")
    print(f"🔑 Nueva contraseña temporal: {password_nueva}")
    print(f"🔁 El usuario deberá cambiarla al iniciar sesión.")
    exportar_pdf(username, password_nueva)

def cambiar_rol_usuario(cur):
    print("\n🎭 Cambiar rol de usuario")

    # Mostrar usuarios actuales
    cur.execute("""
        SELECT u.id, u.username, r.nombre AS rol_actual,
               p.nombre, p.apellido
        FROM usuarios u
        JOIN personas p ON u.persona_id = p.id
        JOIN roles r ON u.rol_id = r.id
        ORDER BY p.apellido, p.nombre;
    """)
    usuarios = cur.fetchall()

    if not usuarios:
        print("⚠️ No hay usuarios registrados.")
        return

    print("\nID | Usuario      | Nombre completo        | Rol actual")
    print("-----------------------------------------------------------")
    for uid, user, rol, nom, ape in usuarios:
        print(f"{uid:<3} {user:<13} {ape.upper()}, {nom:<20} {rol}")

    try:
        uid = int(input("\nID del usuario a modificar: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if uid not in [u[0] for u in usuarios]:
        print("❌ Usuario no encontrado.")
        return

    # Mostrar roles disponibles
    cur.execute("SELECT id, nombre FROM roles ORDER BY nombre;")
    roles = cur.fetchall()

    print("\nRoles disponibles:")
    for rid, nombre in roles:
        print(f"[{rid}] {nombre}")

    try:
        nuevo_rol_id = int(input("ID del nuevo rol: ").strip())
    except ValueError:
        print("❌ ID inválido.")
        return

    if nuevo_rol_id not in [r[0] for r in roles]:
        print("❌ Rol inválido.")
        return

    cur.execute("UPDATE usuarios SET rol_id = %s WHERE id = %s;", (nuevo_rol_id, uid))
    cur.connection.commit()
    print("✅ Rol actualizado correctamente.")

def crear_persona(cur):
    print("\n🆕 Registro de nueva persona")

    dni = input("🪪 DNI: ").strip()
    if not dni:
        print("❌ DNI obligatorio.")
        return

    nombre = input("🧑 Nombre: ").strip().capitalize()
    apellido = input("👤 Apellido: ").strip().capitalize()
    if not nombre or not apellido:
        print("❌ Nombre y apellido son obligatorios.")
        return

    email = input("📧 Email (opcional): ").strip()
    fecha_raw = input("📅 Fecha de nacimiento (AAAA-MM-DD) (opcional): ").strip()

    fecha_nacimiento = None
    if fecha_raw:
        try:
            fecha_nacimiento = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
        except ValueError:
            print("⚠️ Fecha inválida. Se omitirá.")

    try:
        cur.execute("""
            INSERT INTO personas (dni, nombre, apellido, email, fecha_nacimiento, activo)
            VALUES (%s, %s, %s, %s, %s, TRUE);
        """, (dni, nombre, apellido, email or None, fecha_nacimiento))
        cur.connection.commit()
        print("✅ Persona registrada con éxito.")
    except Exception as e:
        cur.connection.rollback()
        print(f"❌ Error al registrar persona: {e}")

def panel_administrador(cur):
    while True:
        print("\n🔧 Panel de gestión de usuarios")
        print("[1] Crear nuevo usuario")
        print("[2] Activar / Inactivar usuario")
        print("[3] Cambiar contraseña de usuario")
        print("[4] Cambiar rol de usuario")
        print("[0] Volver")

        op = input("Opción: ").strip()
        if op == "1":
            crear_usuario(cur)
        elif op == "2":
            activar_inactivar_usuario(cur)
        elif op == "3":
            cambiar_contrasena_usuario(cur)
        elif op == "4":
            cambiar_rol_usuario(cur)
        elif op == "0":
            break
        else:
            print("❌ Opción inválida.")
