# python/routes/files.py

from flask import (
    Blueprint,
    Response,
    flash,
    render_template,
    request,
)

from python.services.system.files import ExcelService, PDFService
from python.services.system.authentication import *
from python.services.system.helper_functions import *
from python.services.dynamic_functions.forms import *
from python.services.dynamic_functions.tables import *
from python.services.system.extensions import csrf

files_bp = Blueprint("files", __name__, url_prefix="/files")

@files_bp.route("/excel/<string:kind>/<string:table>", methods=["GET"])
@login_required
def excel(table,kind):
    """Ruta para generar y descargar un archivo Excel de una table específica."""
    try:
        excel_content, error = ExcelService.generate_excel(table,kind)
        if error:
            flash(f"No se pudo generar el archivo Excel: {error}", "danger")
        response = Response(
            excel_content,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={table}.xlsx"},
        )
        return response
    except Exception as e:
        flash(f"Error inesperado: {str(e)}", "danger")


@files_bp.route("/download_pdf", methods=["Post"])
@csrf.exempt
@login_required
def pdf():
    """Generar y descargar un archivo PDF con los datos de un registro."""
    try:
        table = request.args.get("table")
        id_record = request.args.get("id")

        if not table or not id_record:
            flash(
                "Error: No se proporcionó el nombre de la table o el ID del registro.",
                "danger",
            )
        
        pdf_content, error = PDFService.generate_pdf(table, id_record)

        if error:
            flash(f"No se pudo generar el archivo PDF: {error}", "danger")
        else:
            flash(
                f"El archivo PDF para el registro {id_record} de {table.replace('dynamic/', '').capitalize()} se generó correctamente.",
                "success",
            )

        response = Response(
            pdf_content,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={table}_{id_record}.pdf"
            },
        )
        return response
    except Exception as e:
        flash(f"Error inesperado: {str(e)}", "danger")