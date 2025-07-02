import bcrypt

def cambiar_contrasena_propia(cur, usuario_id):
    print("\n🔑 Cambio de contraseña personal")

    actual = input("Contraseña actual: ").strip()
    nueva = input("Nueva contraseña: ").strip()
    confirmar = input("Confirmar nueva contraseña: ").strip()

    if nueva != confirmar:
        print("❌ Las contraseñas no coinciden.")
        return

    if len(nueva) < 6:
        print("⚠️ La nueva contraseña debe tener al menos 6 caracteres.")
        return

    # Verificar la contraseña actual
    cur.execute("""
        SELECT password_hash FROM usuarios WHERE id = %s;
    """, (usuario_id,))
    fila = cur.fetchone()
    if not fila or not bcrypt.checkpw(actual.encode(), fila[0].encode()):
        print("❌ Contraseña actual incorrecta.")
        return False
    
    # Actualizar nueva contraseña
    hash_nueva = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt()).decode()
    cur.execute("""
        UPDATE usuarios
        SET password_hash = %s,
            debe_cambiar_password = FALSE
        WHERE id = %s;
    """, (hash_nueva, usuario_id))
    cur.connection.commit()

    print("✅ Contraseña actualizada correctamente.")
    return True
