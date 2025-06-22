-- Tabla de categorías de productos
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    codigo_barra VARCHAR(50) NOT NULL UNIQUE,
    precio_compra NUMERIC(10, 2),
    precio_venta NUMERIC(10, 2) NOT NULL,
    stock_actual INTEGER NOT NULL,
    stock_minimo INTEGER,
    foto BYTEA,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
