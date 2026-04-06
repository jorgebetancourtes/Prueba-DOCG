
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for,session

from python.models import db
from python.models.modelos import *
from python.services.system.authentication import *
from sqlalchemy.orm import joinedload
from sqlalchemy import String, Text, or_,func,desc
from datetime import date,timedelta
from python.services.system.helper_functions import *

access_control_bp = Blueprint("access_control", __name__,url_prefix="/access_control")

#####
# pagina principales
#####

@access_control_bp.route("/data_routes/<string:type>/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def rutas(type,id):
    # Obtener parámetros de consulta
    view = request.args.get("view", 50, type=int)
    search = request.args.get("search", "", type=str)
    sortField = request.args.get("sortField", "fecha_de_creacion", type=str)
    sortRule = request.args.get("sortRule", "desc", type=str)
    status = request.args.get("status", "todos", type=str)

    # Iniciar la consulta
    query = Rutas.query

    if status != "todos" and "categoria" in Rutas.__table__.columns:
        query = query.filter(getattr(Rutas, "categoria") == status)

    # Aplicar búsqueda en columnas de type cadena
    if search:
        filters = []

        # Buscar en las columnas de OrdenesDeCompra
        for column in Rutas.__table__.columns:
            if isinstance(column.type, (String, Text)):
                filters.append(column.ilike(f"%{search}%"))

        # Aplicar los filtros al query
        if filters:
            query = query.filter(or_(*filters))

    # Contar el total de registros filtrados
    total = query.count()

    # Aplicar ordenamiento
    if sortField in Rutas.__table__.columns.keys():
        column_attr = getattr(Rutas, sortField)
        if sortRule.lower() == "asc":
            query = query.order_by(column_attr.asc())
        else:
            query = query.order_by(column_attr.desc())
    else:
        query = query.order_by(Rutas.id.asc())

    rol = Roles.query.get(id)
    rutas_en_rol = rol.rutas 
    rutas_en_rol = [record_to_dict(record) for record in rutas_en_rol]
    rutas_en_rol = {record['id'] for record in rutas_en_rol}

    records = query.all()
    items=[]

    if type=='available':
        items = [
            {
                "id": record.id,
                "categoria":record.categoria,
                "nombre": record.nombre,
                "ruta":record.ruta
            }
            for record in records
            if record.id not in rutas_en_rol
        ]
    elif type=='assigned':
        items = [
            {
                "id": record.id,
                "categoria":record.categoria,
                "nombre": record.nombre,
                "ruta":record.ruta
            }
            for record in records
            if record.id in rutas_en_rol
        ]

    pages = (total + view - 1) // view
    
    return jsonify(
        {
            "items": items,
            "total": total,
            "pages": pages,
            "totals": {}
        }
    )

@access_control_bp.route("/data_users/<string:type>/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def usuarios(type,id):
    # Obtener parámetros de consulta
    view = request.args.get("view", 50, type=int)
    search = request.args.get("search", "", type=str)
    sortField = request.args.get("sortField", "fecha_de_creacion", type=str)
    sortRule = request.args.get("sortRule", "desc", type=str)

    # Iniciar la consulta
    query = Usuarios.query

    # Aplicar búsqueda en columnas de type cadena
    if search:
        filters = []

        # Buscar en las columnas de OrdenesDeCompra
        for column in Usuarios.__table__.columns:
            if isinstance(column.type, (String, Text)):
                filters.append(column.ilike(f"%{search}%"))

        # Aplicar los filtros al query
        if filters:
            query = query.filter(or_(*filters))

    # Contar el total de registros filtrados
    total = query.count()

    # Aplicar ordenamiento
    if sortField in Usuarios.__table__.columns.keys():
        column_attr = getattr(Usuarios, sortField)
        if sortRule.lower() == "asc":
            query = query.order_by(column_attr.asc())
        else:
            query = query.order_by(column_attr.desc())
    else:
        query = query.order_by(Usuarios.id.asc())

    records = query.all()
    items=[]
    rol = Roles.query.get(id)

    if type=='available':
        items = [
            {
                "id": record.id,
                "id_rol": record.id_rol,
                "nombre": record.nombre,
                "correo_electronico":record.correo_electronico
            }
            for record in records
            if record.id_rol != rol.id
        ]
    elif type=='assigned':
        items = [
            {
                "id": record.id,
                "id_rol": record.id_rol,
                "nombre": record.nombre,
                "correo_electronico":record.correo_electronico
            }
            for record in records
            if record.id_rol == rol.id
        ]

    pages = (total + view - 1) // view
    
    return jsonify(
        {
            "items": items,
            "total": total,
            "pages": pages,
            "totals": {}
        }
    )

#####
# Roles
#####

# rutas
@access_control_bp.route("/add_access/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def add_access(id):
    rol = Roles.query.get(id)
    cantidad_permisos=rol.rutas.count()
    # Obtener las columnas excluyendo 'fecha_creado'
    columnas = ['categoria','nombre','ruta']

    context = {
        "activeMenu": "permisos",
        "activeItem": "roles",
        "breadcrumbs": [{"name":"Roles","url":url_for("dynamic.table_view", table_name='roles')},{"name":rol.nombre,"url":""}]
    }
    return render_template(
        "system/access_control/add_access.html",
        rol=rol,
        cantidad_permisos=cantidad_permisos,
        columnas=columnas,
        **context
    )

@access_control_bp.route("/add_access_to_role/<id_rol>/<id_ruta>", methods=[ "POST"])
@login_required
@roles_required()
def add_access_to_role(id_rol,id_ruta):
    if request.method == "POST":
        try:
            rol = Roles.query.get(id_rol)
            ruta = Rutas.query.get(id_ruta)
            rol.rutas.append(ruta)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el permiso: {str(e)}", "danger")
    return redirect(url_for("access_control.add_access",id=id_rol))

@access_control_bp.route("/delete_access_to_role/<id_rol>/<id_ruta>", methods=[ "POST"])
@login_required
@roles_required()
def delete_access_to_role(id_rol,id_ruta):
    if request.method == "POST":
        try:
            rol = Roles.query.get(id_rol)
            ruta = Rutas.query.get(id_ruta)
            rol.rutas.remove(ruta)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al eliminar el permiso: {str(e)}", "danger")
    return redirect(url_for("access_control.add_access",id=id_rol))

# usuarios
@access_control_bp.route("/add_users/<id>", methods=["GET", "POST"])
@login_required
@roles_required()
def add_users(id):
    rol = Roles.query.get(id)
    cantidad_usuarios = Usuarios.query.filter_by(id_rol=rol.id).count()
    # Obtener las columnas excluyendo 'fecha_creado'
    columnas = ['nombre','correo_electronico']

    context = {
        "activeMenu": "permisos",
        "activeItem": "usuarios",
        "breadcrumbs": [{"name":"Roles","url":url_for("dynamic.table_view", table_name='roles')},{"name":rol.nombre,"url":""}]
    }
    return render_template(
        "system/access_control/add_users.html",
        rol=rol,
        cantidad_usuarios=cantidad_usuarios,
        columnas=columnas,
        **context
    )

@access_control_bp.route("/add_user_to_role/<id_rol>/<id_usuario>", methods=[ "POST"])
@login_required
@roles_required()
def add_user_to_role(id_rol,id_usuario):
    if request.method == "POST":
        try:
            rol = Roles.query.get(id_rol)
            usuario = Usuarios.query.get(id_usuario)
            usuario.id_rol=rol.id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el usuario: {str(e)}", "danger")
    return redirect(url_for("access_control.add_users",id=id_rol))

@access_control_bp.route("/delete_user_to_role/<id_rol>/<id_usuario>", methods=[ "POST"])
@login_required
@roles_required()
def delete_user_to_role(id_rol,id_usuario):
    if request.method == "POST":
        try:
            usuario = Usuarios.query.get(id_usuario)
            usuario.id_rol=None
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al eliminar el usuario: {str(e)}", "danger")
    return redirect(url_for("access_control.add_users",id=id_rol))
