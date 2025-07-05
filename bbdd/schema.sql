-- Tabla de categorías de productos
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id),
    descripcion TEXT,
    codigo_barra VARCHAR(50) NOT NULL UNIQUE,
    precio_compra NUMERIC(10, 2),
    precio_venta NUMERIC(10, 2),
    stock_actual INTEGER NOT NULL,
    stock_minimo INTEGER,
    foto BYTEA,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'pendiente'
);

-- Tabla principal de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    metodo_pago TEXT  -- Por ahora texto libre; luego puede ser FK
);

-- Detalle por producto vendido en cada venta
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL
);

-- Índice para consultas rápidas por fecha
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_hora);

-- 📦 Registro de aplicaciones instaladas en el ecosistema
CREATE TABLE IF NOT EXISTS sistema_aplicaciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,        -- 'arjenix', 'rrhh', 'bpatient', etc.
    fecha_instalacion DATE DEFAULT CURRENT_DATE,
    version TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- 👥 Personas registradas (núcleo compartido)
CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    dni VARCHAR(15) UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT UNIQUE,
    fecha_nacimiento DATE,
    activo BOOLEAN DEFAULT FALSE,
    foto BYTEA
);

-- 🛡️ Definición de roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,        -- 'dueño', 'vendedor', 'gerente', etc.
    descripcion TEXT
);

-- 🔐 Usuarios del sistema (login)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER UNIQUE REFERENCES personas(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER REFERENCES roles(id),
    ultimo_login TIMESTAMP,
    debe_cambiar_password BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE
);

-- 💡 Tabla opcional para ecosistemas con múltiples módulos activos
-- Permite asignar roles distintos por aplicación (ej: gerente en RRHH, dueño en Arjenix)
CREATE TABLE IF NOT EXISTS permisos_modulo (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    modulo TEXT NOT NULL,                -- Ej: 'arjenix', 'rrhh', 'bpatient'
    rol_id INTEGER REFERENCES roles(id),
    UNIQUE(usuario_id, modulo)
);

-- Insertar roles base
INSERT INTO roles (nombre, descripcion) VALUES
  ('dueño', 'Acceso completo a Arjenix'),
  ('gerente', 'Gestión general de productos y reportes'),
  ('vendedor', 'Realiza ventas y consulta stock'),
  ('repositor', 'Carga stock y gestiona inventario')
ON CONFLICT (nombre) DO NOTHING;

-- Insertar Arjenix como aplicación activa
INSERT INTO sistema_aplicaciones (nombre, version)
VALUES ('arjenix', '1.0')
ON CONFLICT (nombre) DO NOTHING;

