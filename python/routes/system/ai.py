# python/routes/system/ai_query.py

from flask import Blueprint, request, render_template, jsonify,current_app,session
from python.services.system.chat_gpt import QueryService
from python.models.modelos import *
from config import *
from python.services.system.authentication import *

ai_query_bp = Blueprint("ai", __name__, url_prefix="/ai")

def get_service():
    with current_app.app_context():
        return QueryService()

@ai_query_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required()
def ai_html():
    question = request.form.get("question", "")
    return render_template("system/ai_query.html",question=question,title_formats=TITLE_FORMATS)

@ai_query_bp.route("/agent/<question>", methods=["GET"])
@login_required
@roles_required()
def ai_agent(question):
    service = get_service()
    try:
        result = service.ask(question)
        df = result["data"]
        new_record=AiQueries(
            consulta=question,
            sql=result["sql"],
            respuesta=result["answer"],
            id_usuario=session['id_usuario']
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify(
            {"data": 
                {
                    "question":question,
                    "answer":result["answer"],
                    "sql":result["sql"],
                    "columns":df.columns.tolist() if not df.empty else None,
                    "rows":df.to_dict(orient="records") if not df.empty else None
                }
            }
        )
    except Exception as e:
        return jsonify({"data":{"error":"La funcionalidad se encuentra en desarrollo."}})        
        #return jsonify({"data":{"error":str(e)}})