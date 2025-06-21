CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

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