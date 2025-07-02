from modulos.login import *
from modulos.usuarios import *
from modulos.seguridad import *
from bbdd.db_config import *
from modulos.roles import *


def main():
    conn = conectar_db()
    cur = conn.cursor()

    sesion = iniciar_sesion(cur)
    print("🧩 Sesión:", sesion)
    if not sesion:
        print("❌ Falló el inicio de sesión.")
        return

    # ¿Debe cambiar su contraseña?
    if sesion["debe_cambiar_password"]:
        print("\n⚠️ Debés cambiar tu contraseña antes de continuar.")
        ok = cambiar_contrasena_propia(cur, sesion["id"])
        if not ok:
            print("❌ Falló el cambio de contraseña.")
            return
        else:
            print("✅ Contraseña cambiada correctamente. Bienvenido!")
        

    # Delegar según rol
    rol = sesion["rol"]
    if rol == "dueño":
        panel_administrador(cur)
    elif rol == "vendedor":
        menu_vendedor(cur)
    elif rol == "repositor":
        menu_repositor(cur)
    elif rol == "gerente":
        menu_gerente(cur)
    else:
        print(f"⚠️ Rol '{rol}' aún no tiene menú asignado.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
