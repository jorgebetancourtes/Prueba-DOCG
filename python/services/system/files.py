# python/services/files.py

import io

import pandas as pd
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.units import inch
from sqlalchemy.inspection import inspect
import io
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from svglib.svglib import svg2rlg
import os
from python.models import db
from python.services.system.helper_functions import *
from python.services.dynamic_functions.forms import *
from python.services.dynamic_functions.tables import *
from flask import request
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import aliased
from python.services.dynamic_functions.pdf import *
from python.services.system.boto3_s3 import S3Service
from python.services.system.helper_functions import *

s3_service = S3Service()

class ExcelService:
    @staticmethod
    def generate_excel(id_table_name,kind):
        """Exporta los datos de una tabla a un archivo Excel."""
        try:
            params = {}
            params['id_usuario'] = session['id_usuario']
            if kind=='model':
                model = get_model_by_name(id_table_name)

                query,aliased_name_columns,m2m_search_columns,joined_label_names=base_query(model)
                result = query.all()

                columns=get_columns(id_table_name,'main_page')
                if session['nombre_rol']=='Sistema':
                    columns.append('id')                  
                rows = [
                    {col: record_dict[col] for col in columns if col in record_dict}
                    for record_dict in (query_to_dict(record, model) for record in result)
                ]
                sheet_name=id_table_name
            elif kind=='report':
                record=Reportes.query.get(id_table_name)    
                filepath = Archivos.query.filter_by(id_registro=id_table_name).order_by(Archivos.fecha_de_creacion.desc()).first().ruta_s3
                s3 = S3Service()
                query = s3.read_file(filepath)
                variables_query = extract_param_names(query)
                variables_request = {k: v for k, v in request.values.items() if k in variables_query and v != ""}
                result=db.session.execute(text(query),variables_request)
                rows = [dict(row) for row in result.mappings()]
                sheet_name=record.nombre

            if not rows:
                return None, "La tabla no contiene datos."

            df = pd.DataFrame(rows)

            # Exportar a excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)

            output.seek(0)
            return output.getvalue(), None
        except Exception as e:
            return None, str(e)


class PDFService:
    @staticmethod
    def generate_pdf(table_name, id_record):
        try:
            table_name = f"{table_name.split('/')[-1]}"
            # 1) Fetch parent record
            model = get_model_by_name(table_name)
            if not model:
                return jsonify({"error": f"La tabla '{table_name}' no existe."}), 404
            if table_name!='reportes':
                record=model.query.get(id_record)
                result=pdf(f'{table_name}',id_record)
                return result                
            else:
                record=model.query.get(id_record)
                result=pdf(f'reportes_{record.nombre.lower()}',id_record)
                return result

        except SQLAlchemyError as e:
            return None, f"Error de base de datos: {e}"
        except Exception as e:
            return None, str(e)
        