# python/routes/home.py

from flask import Blueprint, render_template,jsonify,request,redirect
from sqlalchemy import or_,and_,cast, String,func,text,extract
from python.models.modelos import *
from python.services.system.boto3_s3 import S3Service
from python.services.system.authentication import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
from python.services.system.extensions import csrf

s3_service = S3Service()

home_bp = Blueprint("home", __name__,url_prefix="/")

@home_bp.route("/", methods=["GET"])
@login_required
def home():
    if session['aplicacion']=='Portal':
        return redirect(url_for("dashboards.portal"))
    elif session['aplicacion']=='Settings':
        return redirect(url_for("dynamic.table_view",table_name='usuarios'))
    
@home_bp.route("/generate-presigned-url/<string:type>", methods=["POST"])
@csrf.exempt
@login_required
def generate_presigned_url(type):
    """
    Genera y retorna una URL firmada para descargar un archivo de S3.
    """
    try:
        id = request.json.get("id")
        filepath=Archivos.query.get(id).ruta_s3
        if not filepath:
            return jsonify({"error": "El campo 'filepath' es obligatorio"}), 400
        presigned_url = s3_service.generate_presigned_url(filepath,type)
        return jsonify({"presigned_url": presigned_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@home_bp.route("/health")
def health():
    return "OK", 200

@home_bp.route("/set_app", methods=["POST"])
@csrf.exempt
def set_app():
    data = request.get_json()
    app = data.get("app")
    if not app:
        return jsonify({"status": "error", "message": "No app"}), 400
    session['aplicacion'] = app
    return jsonify({"status": "success", "app": app})
