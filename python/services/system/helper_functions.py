from python.models.modelos import *
from sqlalchemy import String, Text, or_,func,Integer, Float, Numeric,text
from sqlalchemy.sql import case
from flask import session,flash,request,redirect
import re
import json
from datetime import date, datetime,timedelta
import random
from sqlalchemy import inspect
from config import *
import math
from functools import wraps
from sqlalchemy.orm import aliased
import pandas as pd

#####
# funciones auxiliares
#####

def get_all_models():
    """
    Retorna una lista de todos los modelos registrados en SQLAlchemy
    que tienen asignado el atributo __tablename__.
    """
    models = []
    for model in db.Model.registry._class_registry.values():
        if hasattr(model, "__tablename__"):
            models.append(model)
    return models

def get_model_by_name(table_name):
    """
    Retorna el modelo que corresponde al nombre de la tabla proporcionado.
    Si no se encuentra, retorna None.
    """
    for model in get_all_models():
        if model.__tablename__ == table_name:
            return model
    return None

def sanitize_data(model, data):
    for col in model.__table__.columns:
        if col.name not in data:
            continue
        value = data[col.name]

        if pd.isna(value):
            data[col.name] = None
            continue
        # 🧩 1. Si viene como lista con un solo valor, tomar el primero
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        # 🧩 2. Normaliza booleans
        col_type_str = str(col.type).lower()
        if "bool" in col_type_str:
            if isinstance(value, str):
                val = value.strip().lower()
                if val in ("true", "1", "yes", "on"):
                    value = True
                elif val in ("false", "0", "no", "off", ""):
                    value = False
                else:
                    value = None
        elif "time" in col_type_str:
            if not value:
                value = None
            else:
                try:
                    # First try HH:MM
                    t = datetime.strptime(value, "%H:%M").time()
                except ValueError:
                    try:
                        # Then try HH:MM:SS
                        t = datetime.strptime(value, "%H:%M:%S").time()
                    except ValueError:
                        t = None

                value = t
        elif 'date' in col_type_str:
            if not value:
                value = None                
            else:
                try:
                    if isinstance(value, str):
                        value = str(value.strip())
                        try:
                            value = datetime.strptime(value, "%d/%m/%Y").date()
                        except ValueError:
                            value = datetime.strptime(value, "%Y-%m-%d").date()
                    elif isinstance(value, datetime):
                        value = value.date()
                    elif isinstance(value, date):
                        pass  # already correct
                    else:
                        value = None
                except Exception:
                    value = None
        # 🧩 3. Convierte cadenas vacías según tipo
        elif value == "" or value is None:
            if any(t in col_type_str for t in ["date", "time", "timestamp", "uuid", "json"]):
                value = None
            elif any(t in col_type_str for t in ["int", "numeric", "float", "double", "real"]):
                value = None
            elif any(t in col_type_str for t in ["char", "text", "string"]):
                value = None

        # 🧩 4. Si es numérico, intenta convertirlo correctamente
        elif any(t in col_type_str for t in ["int", "numeric", "float", "double", "real"]):
            try:
                if value == "" or value is None:
                    value = None
                elif "int" in col_type_str:
                    value = int(value)
                else:
                    value = float(value)
            except (ValueError, TypeError):
                value = None  # fallback seguro
        if isinstance(value, float) and math.isnan(value):
            value = None                  
        if col_type_str=='array':
            if value is None:
                value=[]
            elif isinstance(value, str):
                value=[value]
            else:
                value=list(value)     
        data[col.name] = value
    return data

# Función auxiliar para convertir cada registro a diccionario
def record_to_dict(record):
    return {
        col: (
            getattr(record, col).isoformat()
            if hasattr(getattr(record, col), "isoformat")
            else getattr(record, col)
        )
        for col in record.__table__.columns.keys()
    }


# Filtro para formatear fechas
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

    
# Filtro para formatear moneda
def money_format(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value 

def hour_format(value):
    if 'pm' in value.lower() or 'am' in value.lower():
        new_value= datetime.strptime(value.strip().lower(), "%I:%M %p").strftime("%H:%M")
    else:
        try:
            parts = value.strip().split(":")
            new_value=":".join(parts[:2])    
        except:
            new_value=value
    return new_value

def search_table(query, model, search, alias_columns, aggregated_columns):
    """
    Global search across:
      - base model columns
      - joined (direct & nested) alias columns
      - aggregated M2M columns
    """
    filters = []

    alias_columns = alias_columns or []
    aggregated_columns = aggregated_columns or []

    # numeric search?
    try:
        search_number = float(search) if "." in search else int(search)
    except ValueError:
        search_number = None

    # 1) Base model columns
    for col in model.__table__.columns:
        col_attr = getattr(model, col.key)

        if isinstance(col.type, (String, Text)):
            filters.append(col_attr.ilike(f"%{search}%"))

        elif search_number is not None and isinstance(col.type, (Integer, Float, Numeric)):
            filters.append(col_attr == search_number)

    # 2) Joined alias columns (direct & nested)
    for col in alias_columns:
        try:
            col_type = col.type
        except Exception:
            continue

        if isinstance(col_type, (String, Text)):
            filters.append(col.ilike(f"%{search}%"))
        elif search_number is not None and isinstance(col_type, (Integer, Float, Numeric)):
            filters.append(col == search_number)

    # 3) M2M aggregated columns (always text)
    for col in aggregated_columns:
        filters.append(col.ilike(f"%{search}%"))

    if filters:
        query = query.filter(or_(*filters))

    return query

def get_id_visualizacion(table_name):
    modelo = get_model_by_name(table_name)
    prefix = IDS_PREFIXES.get(table_name, "")
    max_id = (modelo.query.with_entities(func.max(modelo.id_visualizacion)).scalar())
    if not max_id:
        next_number = 1
    else:
        try:
            next_number = int(max_id.split("-")[-1]) + 1
        except Exception:
            next_number = 1
    return f"{prefix}-{next_number:09d}"
'''
def get_id_visualizacion(table_name):
    modelo = get_model_by_name(table_name)
    max_id = modelo.query.with_entities(func.max(modelo.id_visualizacion)).scalar()       
    return (max_id or 0) + 1
'''
# queries con variables dinamicas
PARAM_REGEX = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")

def extract_param_names(sql: str) -> set[str]:
    # Find :param placeholders in the SQL
    return set(PARAM_REGEX.findall(sql))

def to_jsonable(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)  # or str(v) if you prefer exact representation
    return v

def rowmapping_to_dict(rm):
    # rm is a RowMapping
    return {k: to_jsonable(v) for k, v in rm.items()}

from decimal import Decimal, InvalidOperation
import re

def parse_money(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(str(value))
    if isinstance(value, str):
        s = value.strip()
        # remove everything except digits, decimal separators, minus sign
        s = re.sub(r'[^0-9,.\-]', '', s)

        # Handle common formats:
        # If there's a comma but no dot, treat comma as decimal sep (e.g., "45,50")
        if ',' in s and '.' not in s:
            s = s.replace('.', '').replace(',', '.')
        else:
            # Otherwise drop thousands commas (e.g., "1,234.56" -> "1234.56")
            s = s.replace(',', '')

        try:
            return float(s)
        except InvalidOperation:
            raise ValueError(f"importe value '{value}' is not a valid number")

def record_to_ordered_list(model, joins, record, columns_order):
    ordered_fields = []

    # Handle Row vs Model instance
    if hasattr(record, "_mapping"):
        record_mapping = record._mapping
        model_instance = record_mapping.get(model, record)
    else:
        record_mapping = {}
        model_instance = record
    mapper = inspect(model_instance.__class__)
    fk_map = {}

    for column in mapper.columns:
        for fk in column.foreign_keys:
            fk_map[column.name] = fk.column.table.name
    # Step 1: Base model columns
    base_data = {}
    for col in model.__table__.columns.keys():
        val = getattr(model_instance, col)
        if isinstance(val, datetime):
            if "fecha" in col.lower():
                val = (val - timedelta(hours=6))
                val = val.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(val, date):
            val = val.strftime('%Y-%m-%d')
        base_data[col] = val

    # Step 2: Add *all* join columns from record_mapping (safe types only)
    for key, value in record_mapping.items():
        if key == model:
            continue  # skip the whole model object
        if isinstance(value, datetime):
            if "fecha" in col.lower():
                value = (value - timedelta(hours=6))
                value = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date):
            value = value.strftime('%Y-%m-%d')    
        elif hasattr(value, "__table__"):  # skip ORM objects
            continue
        base_data[key] = value

    # Step 3: Build ordered output based on config
    if columns_order:
        for col in columns_order:
            # Support dotted notation: Roles.nombre -> id_rol_nombre
            if "." in col:
                table_alias, column_name = col.split(".")
                alias_field = f"id_{table_alias.lower()}_{column_name}"
                value = base_data.get(alias_field)
            else:
                value = f'{base_data.get(col)}'
            if value is not None and value!='None__None':
                ordered_fields.append((col, value))
    else:
        # Default: preserve order of base_data
        ordered_fields = list(base_data.items())

    return ordered_fields

def record_to_ordered_dict(model, record, columns_order):

    if hasattr(record, "_mapping"):
        record_mapping = record._mapping
        model_instance = record_mapping.get(model, record)
    else:
        record_mapping = {}
        model_instance = record

    mapper = inspect(model_instance.__class__)
    fk_map = {}

    for column in mapper.columns:
        for fk in column.foreign_keys:
            fk_map[column.name] = fk.column.table.name
            fk_model = get_model_by_name(fk.column.table.name)
            for col in fk_model.__table__.columns:
                for fk_nested in col.foreign_keys:
                    fk_map[f'{column.name}_{col.name}'] = fk_nested.column.table.name

    # ---------------------------
    # Step 1: Base model columns
    # ---------------------------
    base_data = {}

    for col in model.__table__.columns.keys():
        val = getattr(model_instance, col)

        if isinstance(val, datetime):
            if "fecha" in col.lower():
                val = (val - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(val, date):
            val = val.strftime('%Y-%m-%d')

        base_data[col] = val

    # ---------------------------
    # Step 2: Join columns
    # ---------------------------
    for key, value in record_mapping.items():
        if key == model:
            continue

        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date):
            value = value.strftime('%Y-%m-%d')
        elif hasattr(value, "__table__"):
            continue

        base_data[key] = value
    # ---------------------------
    # Step 3: ORDER-SAFE payload
    # ---------------------------
    payload = []
    if isinstance(columns_order, dict):
        normalized = list(columns_order.items())
    elif isinstance(columns_order, list):
        # No section provided → use a default section name
        normalized = [("informacion_general", columns_order)]
    for section, columns in normalized:
        fields = []
        for col in columns:
            # dotted notation
            if "." in col:
                table_alias, column_name = col.split(".")
                alias_field = f"id_{table_alias.lower()}_{column_name}"
                value = base_data.get(alias_field)

            else:
                # FK formatted fields
                if (
                    col.startswith("id_")
                    and col not in (
                        'id_visualizacion',
                        'id_usuario_correo_electronico',
                        'id_categoria_de_gasto',
                    )
                ):
                    id_col = re.sub(
                        r'_(nombre|descripcion|nombre_completo|id_visualizacion).*$', 
                        '', 
                        col
                    )
                    id_col=id_col.replace('__','_')
                    value = f'{base_data.get(col)}__{base_data.get(id_col)}__{fk_map.get(id_col)}'
                else:
                    value = base_data.get(col)

            if value is not None and value != 'None__None':
                fields.append({
                    "key": col,
                    "value": value
                })

        payload.append({
            "section": section,
            "fields": fields
        })

    return payload


def get_query_variables_values(base_query):
    variables_query = extract_param_names(base_query)
    variables_request = {k: v for k, v in request.values.items() if k in variables_query and v != ""}
    usuario=Usuarios.query.get(session["id_usuario"])
    query_variables={
        "id_usuario":usuario.id,
    }
    for key in query_variables:
        if key in variables_query and query_variables[key] is not None:
            variables_request[key] = query_variables[key]
    return variables_request


def query_to_dict(record,model):
    if hasattr(record, "_mapping"):
        record_mapping = record._mapping
        model_instance = record_mapping.get(model, record)
    else:
        record_mapping = {}
        model_instance = record
    # Base model dict
    model_dict = {}
    for col in model_instance.__table__.columns.keys():
        val = getattr(model_instance, col)
        if isinstance(val, datetime):
            if "fecha" in col.lower():
                val = (val - timedelta(hours=6))
                val = val.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(val, date):
            val = val.strftime('%Y-%m-%d')                 
        model_dict[col] = val
    # Add all join columns (from add_columns)
    for key, value in record_mapping.items():
        # skip the full model object itself (not serializable)
        if isinstance(value, model.__class__):
            continue
        if isinstance(value, datetime):
            if "fecha" in key.lower():
                value = (value - timedelta(hours=6))
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                value = value.strftime('%Y-%m-%d')   
        elif not hasattr(value, "__table__"):  # skip whole ORM objects like Inventario
            model_dict[key] = value
    return model_dict

def generate_pin(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def resolve_foreign_keys_bulk(model, df):
    fk_info = []

    # --- Discover FK metadata ---
    for column in model.__table__.columns:
        for fk in column.foreign_keys:
            local_col = column.name
            ref_table = fk.column.table.name
            ref_pk_col = fk.column.name
            RefModel = get_model_by_name(ref_table)

            if RefModel:
                fk_info.append((local_col, RefModel, ref_pk_col))

    fk_maps = {}

    for local_col, RefModel, ref_pk_col in fk_info:

        if local_col not in df.columns:
            continue

        # 👉 DO NOT force numeric anymore
        df[local_col] = df[local_col].astype(str).str.strip()

        needed_ids = df[local_col].dropna().unique().tolist()

        if not needed_ids:
            continue

        # --- Bulk query ---
        rows = (
            db.session.query(
                RefModel.id_visualizacion,
                getattr(RefModel, ref_pk_col)
            )
            .filter(RefModel.id_visualizacion.in_(needed_ids))
            .all()
        )

        mapping = {str(vis): real_pk for vis, real_pk in rows}

        fk_maps[(local_col, RefModel, ref_pk_col)] = mapping

    # --- Replace values ---
    df = df.copy()

    for local_col, RefModel, ref_pk_col in fk_info:
        if local_col not in df.columns:
            continue

        key = (local_col, RefModel, ref_pk_col)
        mapping = fk_maps.get(key, {})

        col_values = df[local_col].dropna().astype(str)

        missing = set(col_values) - set(mapping.keys())

        if missing:
            raise ValueError(
                f"No se pudieron resolver valores en '{local_col}' "
                f"(tabla '{RefModel.__tablename__}'): {', '.join(missing)}"
            )

        # Replace
        df[local_col] = df[local_col].map(mapping)

        # 👉 Handle UUID columns explicitly
        column_type = str(model.__table__.columns[local_col].type)

        if "UUID" in column_type.upper():
            df[local_col] = df[local_col].apply(
                lambda x: uuid.UUID(str(x)) if pd.notna(x) else None
            )

    return df

def detect_table_from_columns(df_columns):
    normalized = {c.strip() for c in df_columns}

    best_match = None
    best_score = 0

    for table_name, column_map in TABLE_COLUMN_MAPS.items():
        expected = set(column_map.keys())
        score = len(expected & normalized)

        if score > best_score:
            best_match = table_name
            best_score = score

    return best_match if best_score > 0 else None

def deep_getattr(obj, attr, default=None):
    try:
        for part in attr.split('.'):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return default
    
def get_kpi(table_name, sql_name, variables):
    path = f'./static/sql/summary_kpis/{table_name}/{sql_name}.sql'
    base_query = open(path, "r", encoding="utf-8").read()
    variables_query = extract_param_names(base_query)
    variables_request = {
        k: v for k, v in variables.items()
        if k in variables_query and v != ""
    }
    result = db.session.execute(text(base_query), variables_request).fetchone()
    if not result:
        return None  # or 0, or {}
    row = dict(result._mapping)
    return next(iter(row.values()))

def return_url_redirect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)  # 👈 run route FIRST

        return_url = session.pop("return_url", None)
        if return_url:
            return redirect(return_url)

        return response
    return wrapper

def field_changed(changed_fields, field_name):
    if field_name in changed_fields:
        old = changed_fields[field_name]["old"]
        new = changed_fields[field_name]["new"]
        return True, old, new
    return False, None, None

def summarize_changes(changed_fields):
    summary = []
    changed=False
    for field, values in changed_fields.items():
        if values.get("old")!=values.get("new"):
            changed=True
        summary.append((
            field,
            values.get("old"),
            values.get("new")
        ))
    return summary,changed

# dynamic table
def base_query(model):
    query = model.query
    column_map = {}
    # -------------------------------------------------------------------------
    # 1) Many-to-many aggregated columns
    # -------------------------------------------------------------------------
    mapper = inspect(model)
    m2m_search_columns = []
    for rel in mapper.relationships:
        # only many-to-many
        if rel.secondary is None:
            continue
        related_model = rel.mapper.class_
        secondary = rel.secondary
        base_pk = model.__mapper__.primary_key[0]
        related_pk = related_model.__mapper__.primary_key[0]
        base_fk_col = None
        related_fk_col = None
        for col in secondary.c:
            for fk in col.foreign_keys:
                if fk.column is base_pk:
                    base_fk_col = col
                elif fk.column is related_pk:
                    related_fk_col = col
        if base_fk_col is None or related_fk_col is None:
            continue
        display_col_name = next(
            (c.key for c in related_model.__table__.columns
            if c.key in ("nombre", "name", "descripcion")),
            related_pk.key
        )
        display_col = getattr(related_model, display_col_name)
        subq = (
            db.session.query(
                base_fk_col.label("parent_id"),
                func.string_agg(
                    func.cast(display_col, db.String),
                    ", "
                ).label(rel.key)
            )
            .outerjoin(
                related_model,
                related_pk == related_fk_col
            )
            .group_by(base_fk_col)
            .subquery()
        )
        subq_alias = aliased(subq, name=f"{rel.key}_agg")
        query = query.outerjoin(
            subq_alias,
            subq_alias.c.parent_id == base_pk
        )
        agg_col = subq_alias.c[rel.key]
        query = query.add_columns(agg_col)
        m2m_search_columns.append(agg_col)
    # -------------------------------------------------------------------------
    # 2) Restricción por usuario (si no es admin/sistema)
    # -------------------------------------------------------------------------
    from python.services.dynamic_functions.tables import get_rol_fiter
    query=get_rol_fiter(query,model)
    # -------------------------------------------------------------------------
    # 3) Auto + manual joins (direct & nested)
    # -------------------------------------------------------------------------
    joins = get_nested_joins(model, depth=2)
    aliased_name_columns = []
    joined_label_names = set()
    alias_map = {}  # for nested joins: path -> alias
    for field, (table, id_column, name_column) in joins.items():
        parts = field.split("__")
        # Determine parent alias/model and join key
        if len(parts) == 1:
            # Direct join from base model
            parent_alias = model
            join_key = parts[0]
        else:
            # Nested join: join from previously created alias
            parent_path = "__".join(parts[:-1])
            parent_alias = alias_map.get(parent_path)
            if parent_alias is None:
                # parent not joined (not valid for this model), skip
                continue
            join_key = parts[-1]
        # Find FK column on parent_alias safely
        try:
            fk_column = getattr(parent_alias, join_key)
        except AttributeError:
            # parent doesn't have this FK, skip for this model
            continue
        # Create alias for this join target
        alias = aliased(table, name=f"{table.__tablename__}__{field}")
        alias_map[field] = alias
        alias_id_col = getattr(alias, id_column.key)
        # JOIN: alias.id == parent_alias.<fk_column>
        query = query.outerjoin(alias, alias_id_col == fk_column)
        # Expose all columns from joined table
        for col in table.__table__.columns:
            alias_col = getattr(alias, col.key)
            label_name = f"{field}_{col.key}"
            query = query.add_columns(alias_col.label(label_name))
            column_map[label_name] = alias_col
            joined_label_names.add(label_name)
            # For search: only store the "name" column (or the one you chose)
            if col.key == name_column.key:
                aliased_name_columns.append(alias_col)                  
    return query, aliased_name_columns, m2m_search_columns, joined_label_names, column_map

def get_nested_joins(model, depth=2, prefix=""):
    joins = {}
    if depth <= 0:
        return joins

    mapper = inspect(model)

    for rel in mapper.relationships:
        # Only follow MANYTOONE (FKs on this model / on each level)
        if rel.direction.name != "MANYTOONE":
            continue

        related_model = rel.mapper.class_

        # local FK column on the current model/alias (e.g. "id_proyecto")
        local_cols = list(rel.local_columns)
        if not local_cols:
            continue

        local_col = local_cols[0]
        local_key = local_col.key  # e.g. "id_proyecto"

        field_key = prefix + local_key  # e.g. "id_proyecto__id_cliente"

        related_pk = related_model.__mapper__.primary_key[0]

        # choose a "nice" display column
        display_col_name = next(
            (c.key for c in related_model.__table__.columns
             if c.key in ("nombre", "name", "descripcion")),
            related_pk.key
        )

        joins[field_key] = (
            related_model,
            related_pk,
            getattr(related_model, display_col_name)
        )

        # recurse deeper using this related_model
        joins.update(
            get_nested_joins(
                related_model,
                depth=depth - 1,
                prefix=field_key + "__"
            )
        )

    return joins

def apply_filters(query, model, filters, joined_label_names, column_map):
    for key, raw in filters.items():
        if not raw:
            continue

        values = [v.strip() for v in raw.split(",") if v.strip()]
        if not values:
            continue

        # 1) Direct column
        if hasattr(model, key):
            column = getattr(model, key)
            query = query.filter(column.in_(values))
            continue

        # 2) Exact label → real column
        if key in column_map:
            column = column_map[key]
            query = query.filter(column.in_(values))
            continue

        # 3) Smart FK resolution (SAFE now)
        exact_fk = [k for k in column_map if k.endswith(f"__{key}_id")]
        loose_fk = [k for k in column_map if k.endswith(f"_{key}_id")]

        possible_matches = exact_fk or loose_fk

        if possible_matches:
            column = column_map[possible_matches[0]]
            query = query.filter(column.in_(values))

    return query