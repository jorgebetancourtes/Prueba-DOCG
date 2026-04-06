# python/routes/home.py

from flask import Blueprint, render_template, jsonify, request, Response, session
from sqlalchemy import or_, and_, cast, String, func, text
from python.models.modelos import *
from python.services.system.authentication import *
from PIL import Image, ImageDraw, ImageFont
from python.services.system.helper_functions import *
from python.services.system.boto3_s3 import S3Service

s3_service = S3Service()

report_queries_bp = Blueprint("report_queries", __name__, url_prefix="/report_queries")

def get_query_variables_values(base_query):
    variables_query = extract_param_names(base_query)
    variables_request = {k: v for k, v in request.values.items() if k in variables_query and v != ""}
    usuario=Usuarios.query.get(session["id_usuario"])
    query_variables={
        "id_usuario":usuario.id
    }
    for key in query_variables:
        if key in variables_query and query_variables[key] is not None:
            variables_request[key] = query_variables[key]
    return variables_request

@report_queries_bp.route("/<id>", methods=["GET"])
@login_required
@roles_required()
def report_queries(id):
    try:
        context = {
                "activeMenu": 'reportes', 
                "breadcrumbs": [{"name":"Reportes","url":""}]
            }
        record=Reportes.query.get(id)    
        filepath = Archivos.query.filter_by(id_registro=id).order_by(Archivos.fecha_de_creacion.desc()).first().ruta_s3
        s3 = S3Service()
        base_query = s3.read_file(filepath)    
        variables_request=get_query_variables_values(base_query) 
        data=db.session.execute(text(base_query),variables_request)
        columns = list(data.keys())
        return render_template(
            "system/dynamic_table.html",
            columns=columns,
            id=id,
            table_name=record.nombre,
            title_formats=TITLE_FORMATS,
            report=1,
            **context,
        )
    except:
        flash('El reporte no tiene un archivo SQL correcto.','info')
    return redirect(url_for('dynamic.table_view', table_name='reportes'))        

@report_queries_bp.route("/data/<id>", methods=["GET"])
@login_required
@roles_required()
def data(id):
    filepath = Archivos.query.filter_by(id_registro=id).order_by(Archivos.fecha_de_creacion.desc()).first().ruta_s3
    s3 = S3Service()
    base_query = s3.read_file(filepath)    
    variables_request=get_query_variables_values(base_query)
    # --- dynamic table inputs ---
    view      = request.args.get("view", 50, type=int)
    search    = request.args.get("search", "", type=str)
    sortField = request.args.get("sortField", "fecha", type=str)
    sortRule  = request.args.get("sortRule", "desc", type=str)
    page      = request.args.get("page", 1, type=int)
    dateRange=request.args.get("dateRange", "", type=str)

    # 1) get columns from the base query (no rows)
    #    Postgres syntax for subquery alias; adjust alias quoting for other DBs if needed
    probe_sql = text(f"SELECT * FROM ({base_query}) AS base_q LIMIT 0")
    probe_res = db.session.execute(probe_sql, variables_request)
    columns = list(probe_res.keys())
    sortField=''
    # validate sort field
    if 'fecha' in base_query:
        sortField='fecha'
    if 'ultima_interaccion' in base_query:
        sortField='ultima_interaccion'

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

    if dateRange:
        start_str, end_str = dateRange.split(" to ")
        start_date = start_str.strip()
        end_date = end_str.strip()
        params["start_date"] = start_date
        params["end_date"] = end_date
        ands.append("(DATE(fecha) BETWEEN :start_date AND :end_date)")
        
    where_clause = f"WHERE {' AND '.join(ands)}" if ands else ""

    # 3) total count
    count_sql = text(f"""
        SELECT COUNT(*) AS total
        FROM ({base_query}) AS base_q
        {where_clause}
    """)
    total = db.session.execute(count_sql, params).scalar() or 0

    # 4) data page
    params["limit"] = view
    params["offset"] = max(page - 1, 0) * view
    order_clause = f"ORDER BY {sortField} {sortDir}" if sortField else ""
    data_sql = text(f"""
        SELECT *
        FROM ({base_query}) AS base_q
        {where_clause}
        {order_clause}
        LIMIT :limit OFFSET :offset
    """)
    result = db.session.execute(data_sql, params)
    items = [rowmapping_to_dict(rm) for rm in result.mappings().all()]

    return jsonify(
        {
            "items": items,
            "total": total,
            "pages": (total + view - 1) // view, 
        }
    )