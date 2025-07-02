import bcrypt
import psycopg  # psycopg3
from datetime import date

# Datos para el dueño
dni = "12345678"
nombre = "Admin"
apellido = "Principal"
email = "admin@arjenix.com"
fecha_nacimiento = date(1980, 1, 1)
username = "duenio"
password = "123456"

# 👉 Conectá a tu base
conn = psycopg.connect("dbname=arjenix user=postgres password=39416072 host=127.0.0.1 port=5432")
cur = conn.cursor()

# Asegurarse de que el rol 'dueño' exista
cur.execute("SELECT id FROM roles WHERE nombre = 'dueño'")
rol = cur.fetchone()
if rol:
    rol_id = rol[0]
else:
    cur.execute("INSERT INTO roles (nombre, descripcion) VALUES (%s, %s) RETURNING id",
                ('dueño', 'Acceso completo al sistema'))
    rol_id = cur.fetchone()[0]

# Insertar persona
cur.execute("""
    INSERT INTO personas (dni, nombre, apellido, email, fecha_nacimiento, activo)
    VALUES (%s, %s, %s, %s, %s, TRUE)
    RETURNING id
""", (dni, nombre, apellido, email, fecha_nacimiento))
persona_id = cur.fetchone()[0]

# 🔐 Hashear password
password_encriptada = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Insertar usuario
cur.execute("""
    INSERT INTO usuarios (persona_id, username, password_hash, rol_id, activo, debe_cambiar_password)
    VALUES (%s, %s, %s, %s, TRUE, FALSE)
""", (persona_id, username, password_encriptada, rol_id))

conn.commit()
cur.close()
conn.close()

print("✅ Usuario dueño creado correctamente.")
