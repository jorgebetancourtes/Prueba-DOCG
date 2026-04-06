# python/routes/home.py

from flask import Blueprint, render_template, jsonify, request, Response, session
from sqlalchemy import or_, and_, cast, String, func, text
from python.models.modelos import *

from python.services.system.authentication import *
from python.services.system.helper_functions import *

import io
from PIL import Image, ImageDraw, ImageFont


dashboard_queries_bp = Blueprint("dashboard_queries", __name__, url_prefix="/dashboard_queries")

@dashboard_queries_bp.route("/<string:dashboard>/<string:sql_name>", methods=["GET"])
@login_required
@roles_required()
def sql_data(dashboard,sql_name):
    path = f'./static/sql/dashboard_queries/{dashboard}/{sql_name}.sql'
    base_query = open(path, "r", encoding="utf-8").read()
    variables_query = extract_param_names(base_query)
    variables_request = {k: v for k, v in request.values.items() if k in variables_query and v != ""}
    query_variables={
        "id_usuario":session['id_usuario']
    }
    for key in query_variables:
        if key in variables_query and query_variables[key] is not None and key not in variables_request:
            variables_request[key] = query_variables[key]
    if variables_request.get('end_date'):
        end_date = datetime.strptime(variables_request['end_date'], "%Y-%m-%d").date()
        end_date = end_date + timedelta(days=1)
        variables_request['end_date'] = end_date.strftime("%Y-%m-%d")
    data=db.session.execute(text(base_query),variables_request).fetchall()
    data = [dict(row._mapping) for row in data]
    return jsonify(data)

@dashboard_queries_bp.route("/tables/<string:dashboard>/<string:sql_name>", methods=["GET"])
@login_required
def tables_queries(dashboard,sql_name):
    path =f'./static/sql/dashboard_queries/{dashboard}/{sql_name}.sql'
    base_query = open(path, "r", encoding="utf-8").read()
    variables_query = extract_param_names(base_query)
    variables_request = {k: v for k, v in request.values.items() if k in variables_query and v != ""}

    rows = db.session.execute(text(base_query),variables_request).mappings().all()
    data = [dict(row) for row in rows]

    columns = list(rows[0].keys()) if rows else []

    return jsonify({
        "columns": columns,
        "data": data
    })