from datetime import datetime,timedelta
from flask import session
from config import *

# Filtro para formatear números con comas
def commafy(value):
    if value:
        return f"{round(value, 2):,}"
    else:
        return 0

# Filtro para formatear nombres de bases
def title_format(value):
    replacements = TITLE_FORMATS

    if value == "id_visualizacion":
        return "ID"

    # Exact match
    if value in replacements:
        rep = replacements[value]
        if 'id' in value or rep.isupper() or rep[:1].isupper():
            return rep
        return rep[:1].upper() + rep[1:]

    formatted = value.replace("_id_visualizacion", "").replace("_", " ")

    if formatted.startswith("id "):
        formatted = formatted[3:]

    # ⚠️ NO convertir a lower()
    words = formatted.replace('.', ' ').split()

    # Reemplazos sin alterar el resto
    words = [replacements.get(w, w) for w in words]

    if not words:
        return ""

    # ✅ Solo capitalizar la primera palabra
    words[0] = words[0][:1].upper() + words[0][1:]

    return " ".join(words)

# Filtro para formatear nombres de bases
def money_format(value):
    return f"${round(value, 2):,}"

def remove_numbers(value):
    # Convert the value to a string (in case it's a number) and remove all digits
    return ''.join([char for char in str(value) if not char.isdigit()])
    
def date_format(value):
    if not value:
        return value
    meses = [
        "enero", "febrero", "marzo", "abril",
        "mayo", "junio", "julio", "agosto",
        "septiembre", "octubre", "noviembre", "diciembre"
    ]

    dia = value.day
    mes = meses[value.month - 1]
    anio = value.year

    return f"{dia} {mes} de {anio}"

def can_access(path):
    return any(path.startswith(r) for r in session.get("accessible_routes", []))

def local_time(value):
    if not value:
        return ''
    try:
        if isinstance(value, str) and "Fecha hora: " in value:
            value=value.replace('Fecha hora: ', '').strip()
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            value=(value - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M')
            return 'Fecha hora: '+value
        else:
            return (value - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M')
    except Exception as e:
        return ''
