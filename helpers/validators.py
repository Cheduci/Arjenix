import re
from psycopg import Cursor


def validar_email(correo: str) -> bool:
    EMAIL_REGEX = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"

    """Valida formato sintáctico de correo."""
    return bool(re.match(EMAIL_REGEX, correo))

def validar_email_unico(cur: Cursor, correo: str, tabla: str = "personas") -> tuple[bool, str | None]:
    """
    Valida sintaxis y unicidad del correo electrónico.
    Retorna: (es_valido, mensaje_error)
    """
    if not validar_email(correo):
        return False, "El correo ingresado no tiene un formato válido."

    cur.execute(f"SELECT 1 FROM {tabla} WHERE email = %s;", (correo,))
    if cur.fetchone():
        return False, "Ya hay una persona registrada con este correo."

    return True, None
