-- Tabla de categorías
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
    estado VARCHAR(20) DEFAULT 'pendiente',
    proveedor TEXT
);

-- 👥 Personas registradas (núcleo compartido)
CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    dni VARCHAR(15) UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT,
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

-- 🔐 Usuarios 
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER UNIQUE REFERENCES personas(id) ON DELETE CASCADE,
    username varchar(15) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER REFERENCES roles(id),
    ultimo_login TIMESTAMP,
    debe_cambiar_password BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de reposiciones
CREATE TABLE IF NOT EXISTS reposiciones (
    id SERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    motivo TEXT
);

-- Tabla principal de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    metodo_pago TEXT,  -- Por ahora texto libre, luego puede ser FK
    usuario TEXT NOT NULL DEFAULT 'sistema'
);

-- Detalle por producto vendido en cada venta
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    precio_compra NUMERIC(10, 2)
);

-- Tabla datos de la empresa
CREATE TABLE IF NOT EXISTS configuracion_empresa (
    id INTEGER PRIMARY KEY DEFAULT 1,
    nombre TEXT NOT NULL,
    slogan TEXT,
    logo BYTEA
);

-- 📦 Registro de aplicaciones instaladas en el ecosistema
CREATE TABLE IF NOT EXISTS sistema_aplicaciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,        -- 'arjenix', 'rrhh', 'bpatient', etc.
    fecha_instalacion DATE DEFAULT CURRENT_DATE,
    version TEXT,
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

-- Índice para optimizar consultas por producto y rango de fechas
CREATE INDEX IF NOT EXISTS idx_reposiciones_producto_fecha
    ON reposiciones(producto_id, fecha_hora);

-- Índice para consultas rápidas por fecha
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_hora);