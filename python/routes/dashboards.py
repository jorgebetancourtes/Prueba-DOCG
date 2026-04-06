# python/routes/automatizaciones.py

from flask import Blueprint, render_template,jsonify,request
from sqlalchemy import or_,and_,cast, String,func,text,extract
from python.models.modelos import *
from python.services.system.authentication import *
from datetime import datetime


dashboards_bp = Blueprint("dashboards", __name__,url_prefix="/dashboards")
@dashboards_bp.route("/portal", methods=["GET","POST"])
@login_required
def portal():
    data = {'activeMenu': 'inicio'}
    fecha_inicio = date.today().replace(day=1)
    fecha_fin=date.today()
    return render_template('main/dashboards/portal/pagina_principal.html', **data,fecha_inicio=fecha_inicio,fecha_fin=fecha_fin,title_formats=TITLE_FORMATS)

