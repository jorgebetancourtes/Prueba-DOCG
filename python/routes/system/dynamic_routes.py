# python/routes/dynamic_routes.py

from datetime import datetime
from pyexpat import model

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for,session

from python.models import db
from python.models.modelos import *
from python.services.system.helper_functions import *
from python.services.system.template_formats import *
from python.services.form_workflows.edit_on_success import *
from python.services.form_workflows.on_success import *
from python.services.system.authentication import *
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.dynamic import AppenderQuery
from sqlalchemy.orm import aliased
from python.services.dynamic_functions.forms import *
from python.services.dynamic_functions.tables import *
from python.services.system.boto3_s3 import S3Service
from uuid import UUID
import pandas as pd
from io import BytesIO
import xml.etree.ElementTree as ET
import os

s3_service = S3Service()

# Crear un Blueprint para rutas dinámicas basado en el nombre de la tabla
dynamic_bp = Blueprint("dynamic", __name__, url_prefix="/dynamic")


###################
#  Table View
###################

@dynamic_bp.route("/<table_name>/view")
@login_required
@roles_required()
def table_view(table_name):
    session.pop("return_url", None)
    parent_table=request.args.get("parent_table")
    id_parent_record=request.args.get("id_parent_record")
    view_type=request.args.get("view_type")
    model = get_model_by_name(table_name)
    if not model:
        flash(f"La tabla '{table_name}' no existe.", "danger")
        return redirect(request.referrer or url_for("home.home"))

    # Obtener las columnas definidas en el modelo
    columns=get_columns(table_name,'main_page')
    if columns==None:
        columns = model.__table__.columns.keys()

    # Datos para resaltar el menú activo en el sidebar
    module,active_menu=get_breadcrumbs(table_name)
    if module==title_format(table_name):
        breadcrumbs=[{"name":title_format(table_name),"url":""}]
    else:
        breadcrumbs=[{"name":title_format(module),"url":""},{"name":title_format(table_name),"url":""}]
    context = {
            "activeMenu": active_menu, 
            "activeItem": view_type or table_name,
            "breadcrumbs": breadcrumbs
        }
    number_buttons=get_table_buttons(table_name,view_type)
    date_variable=get_calendar_date_variable(table_name)
    javascript = os.path.exists(f'static/js/table_logic/{table_name}.js')
    relationships=get_table_relationships(table_name)
    data_tabs=get_data_tabs(table_name,parent_table,id_parent_record,view_type)
    checkbox=get_checkbox(table_name)
    filter_column=get_filter_column(table_name)
    return render_template(
        "system/dynamic_table.html",
        columns=columns,
        table_name=table_name,
        data_tabs=data_tabs,
        number_buttons=number_buttons,
        date_variable=date_variable,
        id_parent_record=id_parent_record,
        parent_table=parent_table,
        relationships=relationships,
        checkbox=checkbox,
        title_formats=TITLE_FORMATS,
        javascript=javascript,
        html='table',
        filter_column=filter_column,
        **context
    )

@dynamic_bp.route("/<table_name>/data", methods=["GET"], strict_slashes=False)
@login_required
@roles_required()
def data(table_name):
    parent_table = request.args.get("parent_table")
    id_parent_record = request.args.get("id_parent_record")
    view_type=request.args.get("view_type")
    model = get_model_by_name(table_name)
    if not model:
        return jsonify({"error": f"La tabla '{table_name}' no existe."}), 404

    # Parámetros de consulta
    view = request.args.get("view", 50, type=int)
    search = request.args.get("search", "", type=str)
    sortField = request.args.get("sortField", "fecha_de_creacion", type=str)
    sortRule = request.args.get("sortRule", "desc", type=str)
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "todos", type=str)
    dateRange = request.args.get("dateRange", "", type=str)

    # Filtros dinámicos permitidos por tabla
    filters = {}
    filter_column = get_filter_column(table_name)
    for key in request.args:
        if key in filter_column:
            filters[key] = request.args.get(key)

    query, aliased_name_columns, m2m_search_columns, joined_label_names, column_map = base_query(model)

    # -------------------------------------------------------------------------
    # 4) Búsqueda global
    # -------------------------------------------------------------------------
    if search:
        query = search_table(
            query,
            model,
            search,
            aliased_name_columns,
            m2m_search_columns,
        )

    # -------------------------------------------------------------------------
    # 5) Filtros especiales por tabla/padre/estatus
    # -------------------------------------------------------------------------
    if table_name == "archivos":
        query = query.filter(Archivos.id_registro == id_parent_record)

    if parent_table:
        # Filtrado por tabla padre (relación 1-N clásica)
        for rel in model.__mapper__.relationships.values():
            if rel.mapper.local_table.name == parent_table:
                fk = f"id_{rel.key.lower()}"
                if hasattr(model, fk):
                    query = query.filter(getattr(model, fk) == id_parent_record)
                break
    else:
        status_field = get_variable_tabs(table_name)
        if status_field:
            if status != "todos":
                query = query.filter(getattr(model, status_field) == status)
            else:
                open_status = get_open_status(table_name)
                if open_status and hasattr(model, status_field):
                    query = query.filter(
                        getattr(model, status_field).in_(open_status)
                    )
    # filtro view_type
    if view_type:
        query = get_view_type_data_filters(query,table_name,view_type)

    # -------------------------------------------------------------------------
    # 6) Filtro por rango de fechas
    # -------------------------------------------------------------------------
    fecha_fields = get_date_fields()

    if dateRange:
        start_date = end_date = None

        try:
            start_str, end_str = dateRange.split(" to ")
            start_date = datetime.fromisoformat(start_str.strip())
            end_date = datetime.fromisoformat(end_str.strip())
        except ValueError:
            # tal vez es una sola fecha
            try:
                start_date = end_date = datetime.fromisoformat(dateRange.strip())
            except ValueError:
                start_date = end_date = None

        if start_date and end_date:
            # incluir todo el día final
            end_date = end_date + timedelta(days=1)

            conditions = []
            for field in fecha_fields:
                if hasattr(model, field):
                    col = getattr(model, field)
                    conditions.append(col.between(start_date, end_date))

            if conditions:
                query = query.filter(or_(*conditions))

    # -------------------------------------------------------------------------
    # 7) Aplicar filtros de columnas (combo, etc.)
    # -------------------------------------------------------------------------
    query = apply_filters(query, model, filters, joined_label_names, column_map)

    # -------------------------------------------------------------------------
    # 8) Contar registros filtrados (antes de paginación)
    # -------------------------------------------------------------------------
    total = query.count()

    # -------------------------------------------------------------------------
    # 9) Ordenamiento
    # -------------------------------------------------------------------------
    # 1) Sort on joined columns (direct or nested)
    if sortField in joined_label_names:
        query = query.order_by(
            text(f'"{sortField}" {"ASC" if sortRule == "asc" else "DESC"}')
        )

    # 2) Sort on base model column
    elif sortField in model.__table__.columns:
        column_attr = getattr(model, sortField)
        query = query.order_by(
            column_attr.asc() if sortRule == "asc" else column_attr.desc()
        )

    # 3) Fallback
    else:
        query = query.order_by(model.id.asc())

    # -------------------------------------------------------------------------
    # 10) Paginación
    # -------------------------------------------------------------------------
    query = query.offset((page - 1) * view).limit(view)
    records = query.all()

    items = [query_to_dict(record, model) for record in records]

    return jsonify(
        {
            "items": items,
            "total": total,
            "pages": (total + view - 1) // view,
            "totals": {},
        }
    )

@dynamic_bp.route("/<table_name>/form", methods=["GET", "POST"])
@login_required
@roles_required()
def form(table_name):
    parent_table=request.args.get("parent_table")        
    id_parent_record=request.args.get("id_parent_record")    
    form_action=request.args.get("accion")
    model = get_model_by_name(table_name)
    if not model:
        flash(f"La tabla '{table_name}' no existe.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))

    foreign_options = get_foreign_options()
    estatus_options =  get_estatus_options(table_name)
    foreign_options["estatus"] = estatus_options
    form_options=get_form_options(table_name,id_parent_record)
    foreign_options = {**foreign_options, **form_options}
    # Add Many-to-Many relationships
    record_id = request.args.get("id")
    if record_id!=None:
        record = model.query.get(record_id)    
    many_to_many_data = {}
    for attr_name, attr in model.__mapper__.relationships.items():
        if attr.secondary is not None and attr_name!='rutas':  # Ensures it's Many-to-Many
            related_model = attr.mapper.class_

            selected_ids = []
            if record_id!=None:
                selected_items = getattr(record, attr_name, [])
                selected_ids = [item.id for item in selected_items]

            # Get all available options
            all_options = related_model.query.all()

            # Store in dictionary
            many_to_many_data[attr_name] = {
                "selected": selected_ids,
                "options": all_options
            }
    # Add Multiple choice fields
    multiple_choice_data=get_multiple_choice_data()
    modulo,active_menu=get_breadcrumbs(parent_table) if parent_table else get_breadcrumbs(table_name)
    default_variable_values={}
    # edicion
    if record_id!=None:
        name = getattr(record, "nombre", None)
        flujo = request.args.get("accion", None, type=str)
        accion = (f"Editar registro: {name}" if name else "Editar registro: "+ str(record.id_visualizacion)) if flujo is None else (f"{flujo} : {name}" if name else f"{flujo}: "+ str(record.id_visualizacion))
        estatus = getattr(record, "estatus", None) if flujo is None else flujo
        ignored_columns=get_ignored_columns_edit(table_name,estatus)
        columns = [col for col in model.__table__.columns.keys() if col not in ignored_columns]
        non_mandatory_columns=get_non_mandatory_columns(table_name)
        required_fields=[col for col in columns if col not in non_mandatory_columns]
        if not record:
            flash(f"Registro con ID {record_id} no encontrado en '{table_name}'.", "danger")
            return redirect(request.referrer or url_for("dynamic.table_view", table_name=table_name))
        if (record.estatus in get_non_edit_status(table_name) or table_name in get_no_edit_access()) and flujo==None:
            flash(f"Registro ya no se puede editar.", "info")
            return redirect(request.referrer or url_for("dynamic.table_view", table_name=table_name))
        javascript = os.path.exists(f'static/js/form_logic/edit/{table_name}.js')
    else:
        ignored_columns=get_ignored_columns(table_name)
        columns = [col for col in model.__table__.columns.keys() if col not in ignored_columns]
        non_mandatory_columns=get_non_mandatory_columns(table_name)
        required_fields=[col for col in columns if col not in non_mandatory_columns]
        default_variable_values=get_default_variable_values(table_name)
        accion="Registrar"
        record=None
        javascript = os.path.exists(f'static/js/form_logic/add/{table_name}.js')
    if parent_table:
        breadcrumbs=[{"name":modulo,"url":""},{"name":title_format(parent_table),"url":url_for("dynamic.table_view", table_name=parent_table)},{"name":title_format(table_name),"url":url_for("dynamic.table_view", table_name=table_name)},{"name":accion,"url":""}]
    elif modulo==title_format(table_name):
        breadcrumbs=[{"name":title_format(table_name),"url":url_for("dynamic.table_view", table_name=table_name)},{"name":accion,"url":""}]
    else:    
        breadcrumbs=[{"name":modulo,"url":""},{"name":title_format(table_name),"url":url_for("dynamic.table_view", table_name=table_name)},{"name":accion,"url":""}]
    context = {
        "activeMenu": active_menu,
        "activeItem": parent_table if parent_table else table_name,
        "foreign_options": foreign_options,
        "breadcrumbs": breadcrumbs
    }
    form_filters=get_form_filters(table_name)
    parent_record=get_parent_record(table_name,parent_table)
    columns=list(many_to_many_data.keys()) + columns
    columns = [col for col in columns if col not in ignored_columns]
    required_fields = list(many_to_many_data.keys()) + required_fields
    return render_template(
        "system/dynamic_form.html",
        columns=columns,
        required_fields=required_fields,
        table_name=table_name,
        many_to_many_data=many_to_many_data,
        multiple_choice_data=multiple_choice_data,
        action=accion,
        record=record,
        default_variable_values=default_variable_values,
        javascript=javascript,
        form_filters=form_filters,
        parent_record=parent_record,
        parent_table=parent_table,
        id_parent_record=id_parent_record,
        timedelta=timedelta,
        **context,
        form_action=form_action
    )

@dynamic_bp.route("/<table_name>/add", methods=["POST"])
@login_required
@roles_required()
def add(table_name):
    parent_table=request.args.get("parent_table")
    id_parent_record=request.args.get("id_parent_record")    
    model = get_model_by_name(table_name)
    if not model:
        flash(f"La tabla '{table_name}' no existe.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))
    try:
        # Retrieve all form data (handling multi-select fields correctly)
        model_columns = model.__table__.columns.keys() + model.__mapper__.relationships.keys()
        data = {key: request.form.getlist(key) for key in request.form.keys() if key in model_columns}
        data.pop('archivo', None)
        data = sanitize_data(model, data)
        # Extract many-to-many fields (to process separately)
        relationship_data = {}
        normal_data = {}
        for key, value in data.items():
            attr = getattr(model, key, None)
            if isinstance(attr, InstrumentedAttribute) and hasattr(attr.property, "mapper"):
                # This is a relationship field
                relationship_data[key] = value  # Store for later processing
            else:
                # Normal field (use first value if it's a list with one element)
                normal_data[key] = value
        # Create new record with only normal fields first
        new_record = model(**normal_data)
        new_record.id_usuario = Usuarios.query.get(session["id_usuario"]).id
        if hasattr(model, 'id_visualizacion'):
            new_record.id_visualizacion=get_id_visualizacion(table_name)
        if table_name=='archivos':
            new_record.tabla_origen=parent_table
            new_record.id_registro=id_parent_record
            new_record.ruta_s3=''
        if table_name=='usuarios':
            alphabet = string.ascii_letters + string.digits
            contrasena = ''.join(secrets.choice(alphabet) for i in range(20))
            new_record.contrasena=generate_password_hash(contrasena)
            new_record.ultimo_cambio_de_contrasena=datetime.today()
            new_user_email(new_record.correo_electronico,contrasena)
        db.session.add(new_record)
        db.session.flush()
        if table_name=='archivos':
            archivo = request.files.get("archivo")
            s3_service.upload_file(archivo, new_record.id,parent_table)
            new_record.ruta_s3=f"{parent_table}/{ new_record.id}_{archivo.filename}"
            new_record.nombre_del_archivo=archivo.filename
        # Process many-to-many relationships
        for key, value in relationship_data.items():
            related_model = getattr(model, key).property.mapper.class_
            relationship_name=getattr(model, key).key
            selected_ids = [UUID(v) for v in value if v] if value else []
            selected_items = db.session.query(related_model).filter(related_model.id.in_(selected_ids)).all()
            relationship = getattr(new_record, relationship_name)
            relationship.clear()
            relationship.extend(selected_items)              
        # archivos
        archivos = [file for key, file in request.files.items()]
        if archivos and table_name!='archivos':
            for archivo in archivos:
                if archivo.filename:
                    # create file in archivos
                    new_file=Archivos(
                        nombre_del_archivo=archivo.filename,
                        tabla_origen=table_name,
                        id_registro=new_record.id,
                        ruta_s3='',
                        nombre=archivo.name,
                        id_usuario=session['id_usuario']
                    )
                    db.session.add(new_file)
                    db.session.flush()
                    s3_service.upload_file(archivo, new_file.id,table_name)
                    new_file.ruta_s3=f"{table_name}/{new_file.id}_{archivo.filename}"
                    db.session.add(new_file)
                    setattr(new_record, archivo.name, f'{new_file.id}__{archivo.filename}')       
        # Commit transaction
        on_success(table_name,new_record.id)
        db.session.commit()
        flash(f"Registro creado exitosamente en '{title_format(table_name)}'.", "success")    
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear el registro: {str(e)}", "danger")
        return redirect(request.referrer)
    return_url = session.get('return_url')
    if return_url:
        session.pop("return_url", None)
        return redirect(return_url)
    else:
        url=get_url_after_add(table_name)
        if 'double_table_view' in url:
            return redirect(url_for(url, table_name=table_name,id=new_record.id))
        elif 'table_view_input' in url:
            return redirect(url_for(url, main_table_name=table_name,id=new_record.id))        
        else:
            return redirect(url_for(url, table_name=table_name,parent_table=parent_table,id_parent_record=id_parent_record))

@dynamic_bp.route("/<table_name>/delete", methods=["POST"])
@login_required
@roles_required()
def delete(table_name):
    model = get_model_by_name(table_name)
    if not model:
        flash(f"La tabla '{table_name}' no existe.", "danger")
        return redirect(url_for("home.home"))

    record_id = request.args.get("id")  # Obtener como cadena
    if record_id is None:
        flash("No se especificó el ID del registro a eliminar.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))

    # Determinar el tipo de la clave primaria
    primary_key_column = list(model.__table__.primary_key.columns)[0]
    if primary_key_column.type.python_type is int:
        try:
            record_id = int(record_id)
        except ValueError:
            flash("El ID del registro debe ser numérico.", "danger")
            return redirect(url_for("dynamic.table_view", table_name=table_name))

    record = model.query.get(record_id)
    if not record:
        flash(f"Registro con ID {record_id} no encontrado en '{table_name}'.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))

    try:
        db.session.delete(record)
        db.session.commit()
        flash(f"Registro eliminado exitosamente en '{title_format(table_name)}'.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el registro: {str(e)}", "danger")

    return redirect(url_for("dynamic.table_view", table_name=table_name))

@dynamic_bp.route("/<table_name>/edit", methods=["GET", "POST"])
@login_required
@roles_required()
def edit(table_name):
    """
    Endpoint alternativo para editar un registro.
    Se espera recibir el ID del registro a editar mediante un parámetro de query (por ejemplo, ?id=22).
    """
    model = get_model_by_name(table_name)
    if not model:
        flash(f"La tabla '{title_format(table_name)}' no existe.", "danger")
        return redirect(url_for("home.home"))

    record_id = request.args.get("id")
    form_action = request.args.get("form_action")
    if record_id is None:
        flash("No se especificó el ID del registro a editar.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))

    record = model.query.get(record_id)
    if not record:
        flash(f"Registro con ID {record_id} no encontrado en '{table_name}'.", "danger")
        return redirect(url_for("dynamic.table_view", table_name=table_name))

    if request.method == "POST":
        try:
            # Convertir y sanitizar los datos enviados
            data = {key: request.form.getlist(key) for key in request.form.keys()}  # Ensure multi-select fields get all values
            data = sanitize_data(model, data)
            for key, value in data.items():
                if key != "fecha_de_creacion" and hasattr(record, key):
                        attr = getattr(record.__class__, key)
                        # Check if the field is a relationship (Many-to-Many)
                        if isinstance(attr, InstrumentedAttribute) and hasattr(attr.property, 'mapper'):
                            related_model = attr.property.mapper.class_
                            relationship_name=attr.key
                            # Convert selected IDs to integers
                            selected_ids = [UUID(v) for v in value if v] if value else []
                            # Query related objects and update relationship
                            selected_items = db.session.query(related_model).filter(related_model.id.in_(selected_ids)).all()
                            relationship = getattr(record, relationship_name)
                            relationship.clear()
                            relationship.extend(selected_items)                          
                        else:
                            # Assign normal fields
                            setattr(record, key, value)
            # archivos
            archivos = [file for key, file in request.files.items()]
            if archivos:
                for archivo in archivos:
                    if archivo.filename:
                        old_file=Archivos.query.filter_by(id_registro=record.id,nombre=archivo.name,tabla_origen=table_name).first()
                        if old_file:
                            s3_service.delete_file(old_file.ruta_s3)
                            db.session.delete(old_file)
                        # create file in archivos
                        new_record=Archivos(
                            nombre_del_archivo=archivo.filename,
                            tabla_origen=table_name,
                            id_registro=record.id,
                            ruta_s3='',
                            nombre=archivo.name,
                            id_usuario=session['id_usuario']
                        )      
                        db.session.add(new_record)
                        db.session.flush()
                        s3_service.upload_file(archivo, new_record.id,table_name)
                        new_record.ruta_s3=f"{table_name}/{new_record.id}_{archivo.filename}"
                        db.session.add(new_record)
                        setattr(record, archivo.name, f'{new_record.id}__{archivo.filename}')   
            state = inspect(record)
            changed_fields = {
                attr.key: {
                    "old": str(attr.history.deleted[0]) if attr.history.deleted else None,
                    "new": str(attr.history.added[0]) if attr.history.added else None
                }
                for attr in state.attrs
                if attr.history.has_changes()
            }
            db.session.flush()
            edit_on_success(table_name, record.id, changed_fields,form_action)            
            db.session.commit()
            flash(f"Registro actualizado exitosamente en '{title_format(table_name)}'.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el registro: {str(e)}", "danger")
        return_url = session.get('return_url')
        if return_url:
            session.pop("return_url", None)
            return redirect(return_url)
        else:
            return redirect(url_for("dynamic.table_view", table_name=table_name))

@dynamic_bp.route("/<table_name>/data/<id_record>", methods=["GET"])
@login_required
@roles_required()
def record_data(table_name, id_record):
    model = get_model_by_name(table_name)
    if not model:
        return jsonify({"error": f"La tabla '{table_name}' no existe."}), 404

    query = model.query
    mapper = inspect(model)

    # -------------------------------------------------------------------------
    # 1) Many-to-many aggregated columns
    # -------------------------------------------------------------------------
    for rel in mapper.relationships:
        if rel.secondary is None:
            continue  # only many-to-many

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
                func.string_agg(func.cast(display_col, db.String), ", ").label(rel.key)
            )
            .outerjoin(related_model, related_pk == related_fk_col)
            .group_by(base_fk_col)
            .subquery()
        )

        subq_alias = aliased(subq, name=f"{rel.key}_agg")
        query = query.outerjoin(subq_alias, subq_alias.c.parent_id == base_pk)
        query = query.add_columns(subq_alias.c[rel.key])

    # -------------------------------------------------------------------------
    # 2) Auto + manual joins (supports nested)
    # -------------------------------------------------------------------------
    joins = get_nested_joins(model, depth=2)

    alias_map = {}
    aliased_name_columns = []  # used by modal formatting if needed

    for field, (table, id_column, name_column) in joins.items():
        parts = field.split("__")

        # Determine parent (base model or alias)
        if len(parts) == 1:
            parent_alias = model
            join_key = parts[0]
        else:
            parent_path = "__".join(parts[:-1])
            parent_alias = alias_map.get(parent_path)
            if parent_alias is None:
                continue
            join_key = parts[-1]

        # FK column on parent alias
        try:
            fk_column = getattr(parent_alias, join_key)
        except AttributeError:
            continue

        # Current table alias
        alias = aliased(table, name=f"{table.__tablename__}__{field}")
        alias_map[field] = alias

        alias_id_col = getattr(alias, id_column.key)

        query = query.outerjoin(alias, alias_id_col == fk_column)

        # Add all columns from the joined table
        for col in table.__table__.columns:
            alias_col = getattr(alias, col.key)
            label_name = f"{field}_{col.key}"
            query = query.add_columns(alias_col.label(label_name))

            # Keep "name-like" column for display/search
            if col.key == name_column.key:
                aliased_name_columns.append(alias_col)

    # -------------------------------------------------------------------------
    # 3) Filter by record id
    # -------------------------------------------------------------------------
    query = query.filter(model.id == id_record)

    records = query.all()

    # -------------------------------------------------------------------------
    # 4) Format results for the modal
    # -------------------------------------------------------------------------
    columns_order = get_columns(table_name, "modal")
    record = [record_to_ordered_dict(model, r, columns_order) for r in records]

    # -------------------------------------------------------------------------
    # 5) Relationship section (lower pane)
    # -------------------------------------------------------------------------
    relationships = get_table_relationships(table_name)
    if relationships and record:
        relationships_section = {
            "section": "registros_relacionados",
            "fields": [
                {
                    "key": "detalle",
                    "value": (
                        f"/dynamic/{table_name}/related/{id_record}/{relationships[0]}"
                        f"?parent_table={table_name}&id_parent_record={id_record}"
                    )
                }
            ],
        }
        record[0].append(relationships_section)
    return jsonify(record)

###################
# Double Table View
###################

@dynamic_bp.route("/<string:table_name>/double_table/view/<id>")
@login_required
@roles_required()
def double_table_view(table_name,id):
    model = get_model_by_name(table_name)
    record = model.query.get(id)
    variables=get_variables_double_table_view(table_name)
    columns_first_table = variables.get('columns_first_table')
    columns_second_table = variables.get('columns_second_table')
    title_first_table= variables.get('title_first_table')
    title_second_table= variables.get('title_second_table')
    model_first_table=variables.get('model_first_table')
    model_second_table=variables.get('model_second_table')
    edit_fields=variables.get('edit_fields')
    required_fields=variables.get('required_fields')
    foreign_options = get_foreign_options()
    form_options=get_form_options(table_name,record.id)
    foreign_options = {**foreign_options, **form_options}
    details = []   
    details = { detail:deep_getattr(record, detail) for detail in variables.get('details', [])}

    module,active_menu=get_breadcrumbs(table_name)
    context = {
                "activeMenu": active_menu, 
                "activeItem": table_name,
                "breadcrumbs": [{"name":module,"url":""},{"name":title_format(table_name),"url":""}]
            }
    return render_template(
        "system/dynamic_two_table_view.html",
        table_name=table_name,
        id_main_record=record.id,
        main_record=record,
        columns_first_table=columns_first_table,
        columns_second_table=columns_second_table,
        title_first_table=title_first_table,
        title_second_table=title_second_table,
        model_first_table=model_first_table,
        model_second_table=model_second_table,
        details=details,
        edit_fields=edit_fields,
        required_fields=required_fields,
        html='table',
        foreign_options=foreign_options,
        title_formats=TITLE_FORMATS,
        **context
    )

@dynamic_bp.route("/<string:table_name>/double_table/data/<string:table>/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def double_table_view_data(table,table_name,id):
    variables=get_variables_double_table_view(table_name)
    if table=='first':
        sql_name= variables.get('query_first_table')
    elif table=='second':
        sql_name= variables.get('query_second_table')

    path = f'./static/sql/double_table_queries/{table_name}/{sql_name}.sql'
    base_query = open(path, "r", encoding="utf-8").read()
    variables_request={'id_main_record':id}
    # --- dynamic table inputs ---
    search    = request.args.get("search", "", type=str)
    sortRule  = request.args.get("sortRule", "desc", type=str)
    sortField  = request.args.get("sortField", "fecha_de_creacion", type=str)

    # 1) get columns from the base query (no rows)
    #    Postgres syntax for subquery alias; adjust alias quoting for other DBs if needed
    probe_sql = text(f"SELECT * FROM ({base_query}) AS base_q LIMIT 0")
    probe_res = db.session.execute(probe_sql, variables_request)
    columns = list(probe_res.keys())

    # validate sort field
    sortDir = "ASC" if sortRule.lower() == "asc" else "DESC"

    # 2) build WHERE for search (case-insensitive). For Postgres, use ILIKE + CAST.
    where_clause = ""
    params = dict(variables_request)
    ands = []
    if search:
        like_param = f"%{search}%"
        params["search"] = like_param
        ors = " OR ".join([f"CAST({col} AS TEXT) ILIKE :search" for col in columns])
        ands.append(f"({ors})")

    where_clause = f"WHERE {' AND '.join(ands)}" if ands else ""

    # 4) data page
    data_sql = text(f"""
        SELECT *
        FROM ({base_query}) AS base_q
        {where_clause}
        ORDER BY {sortField} {sortDir}
    """)
    result = db.session.execute(data_sql, params)
    items = [rowmapping_to_dict(rm) for rm in result.mappings().all()]
    return jsonify({"items": items})

@dynamic_bp.route("/<string:main_table_name>/double_table/add/<string:first_table>/<string:second_table>/<id_main_record>/<id_record>", methods=[ "POST"])
@login_required
def double_table_add(main_table_name,first_table,second_table,id_main_record,id_record):
    if request.method == "POST":
        try:
            main_model=get_model_by_name(main_table_name)
            main_record = main_model.query.get(id_main_record)
            model=get_model_by_name(first_table)
            record = model.query.get(id_record)
            record_id=record.id if record else id_record
            new_record=add_record_double_table(main_table_name,second_table,main_record.id,record_id)
            db.session.add(new_record)
            db.session.flush()
            on_add_double_table(main_table_name,id_main_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el registro: {str(e)}", "danger")
    return redirect(url_for("dynamic.double_table_view",table_name=main_table_name,id=id_main_record))

@dynamic_bp.route("/<string:main_table_name>/double_table/delete/<string:table_name>/<id_main_record>/<id>", methods=[ "POST"])
@login_required
def delete_double_table(main_table_name,table_name,id,id_main_record):
    if request.method == "POST":
        try:
            model=get_model_by_name(table_name)
            record = model.query.get(id)
            validation=validate_delete(table_name,id)
            if validation:
                on_delete_double_table(table_name,id)
                db.session.delete(record)
                db.session.flush()
                on_delete_double_table(main_table_name,id_main_record)
                db.session.commit()
                message=''
                status='success'                
            else:
                message='El registro no puede ser eliminado'
                status='warning'
        except Exception as e:
            db.session.rollback()
            flash(f"Error al eliminar el registro: {str(e)}", "danger")
        return jsonify({"status": status, "message": message})

@dynamic_bp.route("/<string:table_name>/double_table/update/<string:column>/<id>", methods=["POST"])
@dynamic_bp.route("/<string:table_name>/double_table/update/<string:column>/<id>/<value>", methods=[ "POST"])
@login_required
@csrf.exempt
def double_table_update(table_name,column,id,value=0):
    try:
        value_warning=''
        model=get_model_by_name(table_name)
        record = model.query.get(id)
        validation=get_update_validation(table_name,record,column,value)
        if validation['status']==0:
            message=validation['message']
            status='warning'
            value_warning=validation['value_warning']
        else:
            setattr(record, column, value)
            db.session.flush()
            on_update_double_table(table_name,id)
            db.session.commit()
            message='El valor se ha actualizado correctamente.'
            status='success'
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el valor: {str(e)}", "danger")
    return jsonify({"status": status, "message": message,"value":value_warning})

@dynamic_bp.route("/double_table/reload_details/<string:main_table_name>/<id>", methods=["GET"])
@login_required
@roles_required()
def double_table_reload_details(main_table_name, id):
    model = get_model_by_name(main_table_name)
    record = model.query.get(id)
    variables = get_variables_double_table_view(main_table_name)
    ordered_details = []
    for detail in variables.get('details', []):
        ordered_details.append({
            "key": detail,
            "value": deep_getattr(record, detail)
        })
    return jsonify({"details": ordered_details})

###############
#  Table View Input
###################

@dynamic_bp.route("/input_table/reload_details/<string:main_table_name>/<id>", methods=["GET"])
@login_required
@roles_required()
def input_table_reload_details(main_table_name, id):
    model = get_model_by_name(main_table_name)
    record = model.query.get(id)
    variables = get_variables_table_view_input(main_table_name)
    ordered_details = []
    for detail in variables.get('details', []):
        ordered_details.append({
            "key": detail,
            "value": deep_getattr(record, detail)
        })
    return jsonify({"details": ordered_details})

@dynamic_bp.route("/<string:main_table_name>/input_table/view/<id>")
@login_required
@roles_required()
def table_view_input(main_table_name,id):
    model = get_model_by_name(main_table_name)
    record = model.query.get(id)
    variables=get_variables_table_view_input(main_table_name)
    columns = variables.get('columns')
    table_title = variables.get('table_title')
    table_name = variables.get('table_name')
    edit_fields=variables.get('edit_fields')
    required_fields=variables.get('required_fields')
    delete_button=variables.get('delete_button')
    add_button=variables.get('add_button')
    foreign_options = get_foreign_options()
    form_options=get_form_options(table_name,record.id)
    foreign_options = {**foreign_options, **form_options}
    details = []   
    details = { detail:deep_getattr(record, detail) for detail in variables.get('details', [])}
        
    module,active_menu=get_breadcrumbs(table_name)
    context = {
                "activeMenu": active_menu, 
                "activeItem": main_table_name,
                "breadcrumbs": [{"name":module,"url":""},{"name":title_format(table_name),"url":""}]
            }
    session['return_url']=request.url
    return render_template(
        "system/dynamic_table_input.html",
        table_name=table_name,
        main_table_name=main_table_name,
        id_main_record=record.id,
        main_record=record,
        columns=columns,
        table_title=table_title,
        html='table',
        edit_fields=edit_fields,
        required_fields=required_fields,
        foreign_options=foreign_options,
        details=details,
        delete_button=delete_button,
        add_button=add_button,
        title_formats=TITLE_FORMATS,
        **context
    )

@dynamic_bp.route("/<string:table_name>/input_table/data/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def table_view_input_data(table_name,id):
    variables=get_variables_table_view_input(table_name)
    sql_name= variables.get('query_table')
    path = f'./static/sql/input_table_queries/{table_name}/{sql_name}.sql'
    base_query = open(path, "r", encoding="utf-8").read()
    variables_request={'id_main_record':id}
    # --- dynamic table inputs ---
    search    = request.args.get("search", "", type=str)
    sortRule  = request.args.get("sortRule", "desc", type=str)

    probe_sql = text(f"SELECT * FROM ({base_query}) AS base_q LIMIT 0")
    probe_res = db.session.execute(probe_sql, variables_request)
    columns = list(probe_res.keys())

    sortField = 'fecha_de_creacion'
    sortDir = "ASC" if sortRule.lower() == "asc" else "DESC"

    # 2) build WHERE for search (case-insensitive). For Postgres, use ILIKE + CAST.
    where_clause = ""
    params = dict(variables_request)
    ands = []
    if search:
        like_param = f"%{search}%"
        params["search"] = like_param
        ors = " OR ".join([f"CAST({col} AS TEXT) ILIKE :search" for col in columns])
        ands.append(f"({ors})")

    where_clause = f"WHERE {' AND '.join(ands)}" if ands else ""

    # 4) data page
    data_sql = text(f"""
        SELECT *
        FROM ({base_query}) AS base_q
        {where_clause}
        ORDER BY {sortField} {sortDir}
    """)
    result = db.session.execute(data_sql, params)
    items = [rowmapping_to_dict(rm) for rm in result.mappings().all()]
    return jsonify(
        {
            "items": items,
        }
    )

@dynamic_bp.route("/<string:table_name>/input_table/confirm/<id>")
@login_required
@roles_required()
def table_view_input_confirm(table_name,id):
    variables = get_variables_table_view_input(table_name)
    url_confirm=variables.get('url_confirm')
    return redirect(url_for(url_confirm, id=id))

@dynamic_bp.route("/<string:table_name>/double_table/confirm/<id>")
@login_required
@roles_required()
def double_table_view_confirm(table_name,id):
    variables = get_variables_double_table_view(table_name)
    url_confirm=variables.get('url_confirm')
    return redirect(url_for(url_confirm, id=id))


###################
# Import data 
###################

@dynamic_bp.route("/import_data/<string:table_name>", methods=["POST"])
@login_required
@roles_required()
def import_data(table_name):
    file = request.files.get("archivo")
    if not file:
        flash("No se seleccionó ningún archivo.", "info")
        return redirect(url_for('dynamic.table_view', table_name=table_name))

    model = get_model_by_name(table_name)
    if model is None:
        return jsonify({'alert':'info','message': f"La tabla '{table_name}' no existe."})
    try:
        # --- Read file ---
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            return jsonify({'alert':'info','message': "El archivo debe ser CSV o XLSX."})
        map = TABLE_COLUMN_MAPS.get(table_name)
        if map:
            df.columns = df.columns.str.strip()

            # --- Auto detect table ---
            table_name = detect_table_from_columns(df.columns)
            if not table_name:
                return jsonify({
                    "alert": "error",
                    "message": "No se pudo detectar la tabla automáticamente."
                })
                
            model = get_model_by_name(table_name)
            column_map = TABLE_COLUMN_MAPS[table_name]
            # --- Rename columns ---
            if column_map:
                df = df.rename(columns=column_map)
        # --- Validate required columns ---
        model_columns = {c.name for c in model.__table__.columns}

        required_columns = {
            c.name
            for c in model.__table__.columns
            if not c.nullable and not c.primary_key
        }

        file_columns = set(df.columns)
        missing_cols = required_columns - file_columns - {
            'estatus', 'id_usuario', 'id', 'fecha_de_actualizacion',
            'fecha_de_creacion', 'id_visualizacion'
        }

        if missing_cols:
            return jsonify({'alert':'info','message': f"Faltan columnas requeridas: {', '.join(missing_cols)}"})

        def chunks(seq, size):
            for i in range(0, len(seq), size):
                yield seq[i:i+size]

        df = resolve_foreign_keys_bulk(model, df)
        df = df.where(pd.notna(df), None)

        id_visualizacion = get_id_visualizacion(table_name)
        id_usuario = session["id_usuario"]

        # Extract prefix and starting number once
        prefix, numero = id_visualizacion.split("-")
        numero = int(numero)

        model_cols = set(model_columns)
        cols = [c for c in df.columns if c in model_cols]

        rows = list(df[cols].itertuples(index=False, name=None))

        for batch in chunks(rows, 2000):
            mappings = []
            for row in batch:
                clean = dict(zip(cols, row))
                clean = sanitize_data(model, clean)
                clean["id_visualizacion"] = f"{prefix}-{numero:09d}"
                clean["id_usuario"] = id_usuario
                mappings.append(clean)
                # Increment for next row
                numero += 1

            db.session.bulk_insert_mappings(model, mappings)
        db.session.commit()
        return jsonify({'alert':'success','message': f"Se importaron {len(df)} registros."})

    except Exception as e:
        db.session.rollback()
        return jsonify({'alert':'error','message': f"Error en la importación: {e}"})

###################
# Upload specific files (double table/input table)
###################

@dynamic_bp.route("/upload_file/<string:table_name>/<id>/<column>", methods=["POST"])
@login_required
def upload_file(table_name,id,column):
    model=get_model_by_name(table_name)
    record=model.query.get(id)
    old_file=Archivos.query.filter_by(id_registro=id,nombre=column,tabla_origen=table_name).first()
    if old_file:
        s3_service.delete_file(old_file.ruta_s3)
        db.session.delete(old_file)
    # create file in archivos
    archivo = request.files.get("archivo")
    new_record=Archivos(
        nombre_del_archivo=archivo.filename,
        tabla_origen=table_name,
        id_registro=id,
        ruta_s3='',
        nombre=column,
        id_usuario=session['id_usuario']
    )
    db.session.add(new_record)
    db.session.flush()
    s3_service.upload_file(archivo, new_record.id,table_name)
    new_record.ruta_s3=f"{table_name}/{new_record.id}_{archivo.filename}"
    db.session.add(new_record)
    setattr(record, column, f'{new_record.id}__{archivo.filename}')
    db.session.commit()
    return jsonify({'alert':'success','message': f"El archivo se cargo exitosamente."})

###################
# Related tables view
###################

@dynamic_bp.route("/<parent_table>/related/<id>/<table_name>", methods=["GET"])
@login_required
def related(id,parent_table,table_name):
    session['return_url'] = request.url
    model=get_model_by_name(parent_table)
    id_parent_record=id
    record=model.query.get(id)
    modulo,active_menu=get_breadcrumbs(parent_table)
    parent_record_name = getattr(record, "nombre", None) or getattr(record, "nombre_completo", None) or getattr(record, "pregunta", None) or getattr(record, "id_visualizacion", None)   
    if modulo==title_format(parent_table):
        breadcrumbs=[{"name":title_format(parent_table),"url":url_for("dynamic.table_view", table_name=parent_table)},{"name":parent_record_name,"url":""}]
    else:
        breadcrumbs=[{"name":modulo,"url":""},{"name":title_format(parent_table),"url":url_for("dynamic.table_view", table_name=parent_table)},{"name":parent_record_name,"url":""}]
    context = {
        "activeMenu": active_menu,
        "activeItem": parent_table,
        "breadcrumbs": breadcrumbs
    }
    variables=get_summary_data(parent_table)
    primary=[]
    primary_info=[]
    name=''
    if variables:
        primary = variables.get('primary',[])
        primary_info = [ deep_getattr(record, detail) for detail in primary]
        name=deep_getattr(record, variables.get('primary', [])[0])
    if table_name=='resumen':
        record_data = {}
        data = variables.get('data', {})
        for section, details in data.items():
            record_data[section] = {
                detail: deep_getattr(record, detail)
                for detail in details
            }
        kpis=get_summary_kpis(parent_table,id_parent_record)
        return render_template(
            "system/dynamic_summary.html",
            record=record,
            title_formats=TITLE_FORMATS,
            parent_table=parent_table,
            id_parent_record=id_parent_record,
            activeDefTab=table_name,
            tabs=get_table_relationships(parent_table), 
            primary_info=primary_info,  
            record_data=record_data,
            kpis=kpis,
            nombre=name,
            **context
        )
    else:
        number_buttons=get_table_buttons(table_name,view_type='default')
        date_variable=get_calendar_date_variable(table_name)
        javascript = os.path.exists(f'static/js/table_logic/{table_name}.js')
        checkbox=get_checkbox(table_name)    
        return render_template(
            "system/dynamic_related_data.html",
            record=record,
            title_formats=TITLE_FORMATS,
            table_name=table_name,
            columns=get_columns(table_name,'main_page'),
            parent_table=parent_table,
            id_parent_record=id_parent_record,
            activeDefTab=table_name,
            tabs=get_table_relationships(parent_table),
            number_buttons=number_buttons,
            date_variable=date_variable,
            checkbox=checkbox,
            javascript=javascript,
            primary_info=primary_info,
            nombre=name,
            **context        
        )
