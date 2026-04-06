# python/routes/home.py

from flask import Blueprint, render_template, jsonify, request, Response, session
from sqlalchemy import or_, and_, cast, String, func, text
from python.models.modelos import *
from python.services.system.authentication import *

import io
from PIL import Image, ImageDraw, ImageFont
from python.services.dynamic_functions.forms import *
from python.services.dynamic_functions.tables import *
import traceback

api_bp = Blueprint("api", __name__, url_prefix="/api")
def api_login(json_data):
    id_usuario = json_data.get('id_usuario')
    contrasena = json_data.get('contrasena')
    user = Usuarios.query.filter(Usuarios.id==id_usuario).first()
    if user!=None:
        if contrasena==str(user.contrasena_api):
            data={'message':'Credenciales validas'}
        else:
            data={'message':'Credenciales no validas'}
    else:
        data={'message':'Credenciales no validas'}
    return data  # Redirect back to the form

@api_bp.route('/<table_name>',methods=['GET', 'POST'])
def dynamic_data(table_name):
    json_data = request.json
    auth=api_login(json_data)
    if auth['message']=='Credenciales validas':
        model = get_model_by_name(table_name)
        if not model:
            data={'message':'La tabla no existe.'}
            return data
        data = [item.to_dict() for item in model.query.all()]
        return jsonify(data)
    else:
        data={'message':'Credenciales no validas'}
        return data
