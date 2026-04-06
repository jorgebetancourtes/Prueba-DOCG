
from python.models.modelos import *
import io

import pandas as pd
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter,landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER,TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image,KeepTogether
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
from datetime import datetime

#####
# funciones de formularios
#####

HANDLERS = {}

def handler_pdf(*tables):
    def wrapper(fn):
        for t in tables:
            HANDLERS[t] = fn
        return fn
    return wrapper

def pdf(table_name, id):
    handler = HANDLERS.get(table_name)
    if not handler:
        logo_path= "./static/images/logo-light.png"
        model = get_model_by_name(table_name)
        # Iniciar la consulta
        query = model.query
        # Agregar joins condicionales
        joins = get_nested_joins(model, depth=2)
        for field, (table, id_column, name_column) in joins.items():
            # Asegura que el campo exista en el modelo base
            if field not in model.__table__.columns:
                continue

            # Crea un alias único por campo (soporta varias uniones al mismo modelo)
            alias = aliased(table, name=f"{table.__tablename__}__{field}")

            # Re-vincula columnas al alias
            alias_id_col = getattr(alias, id_column.key)
            alias_name_col = getattr(alias, name_column.key)

            # Join explícito y ON explícito contra el modelo base
            query = (
                query.outerjoin(alias, alias_id_col == getattr(model, field))
                    .add_columns(alias_name_col.label(f"{field}_{name_column.key}"))
            )
        query=query.filter(model.id == id)
        records = query.all()
        columns_order=get_columns(table_name,'pdf')
        print(records)
        record = [record_to_ordered_list(model,joins,record,columns_order) for record in records]
        record = dict(record[0])
        print(record)
        # 2) Collect relationship data (all rows for each related table)
        parent_model = get_model_by_name(table_name)
        relationships = get_table_relationships(table_name)
        if relationships:
            relationship_table_name=relationships[0]
            related_model = get_model_by_name(relationship_table_name)
            fk_name = None
            for relationships[0], rel in inspect(related_model).relationships.items():
                if rel.mapper.class_ is parent_model:
                    # FK column(s) on the related model
                    local_fk_cols = [c.name for c in rel.local_columns]
                    if local_fk_cols:
                        fk_name = local_fk_cols[0]
                        break
            # Iniciar la consulta
            query = related_model.query
            # Agregar joins condicionales
            joins = get_nested_joins(model, depth=2)
            for field, (table, id_column, name_column) in joins.items():
                # Asegura que el campo exista en el modelo base
                if field not in related_model.__table__.columns:
                    continue

                # Crea un alias único por campo (soporta varias uniones al mismo modelo)
                alias = aliased(table, name=f"{table.__tablename__}__{field}")

                # Re-vincula columnas al alias
                alias_id_col = getattr(alias, id_column.key)
                alias_name_col = getattr(alias, name_column.key)

                # Join explícito y ON explícito contra el modelo base
                query = (
                    query.outerjoin(alias, alias_id_col == getattr(related_model, field))
                        .add_columns(alias_name_col.label(f"{field}_{name_column.key}"))
                )
            query=query.filter(getattr(related_model, fk_name) == id)
            related_records = query.all()
            columns_order=get_columns(relationship_table_name,'pdf')
            related_records = [record_to_ordered_list(related_model,joins,record,columns_order) for record in related_records]
            all_related_results = related_records
        # 3) Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(name="Title", fontSize=16, alignment=TA_CENTER, spaceAfter=8)
        section_title_style = ParagraphStyle(name="SectionTitle", fontSize=13, alignment=TA_LEFT, spaceBefore=12, spaceAfter=6)
        cell_style = ParagraphStyle(name="Cell", fontSize=9, alignment=TA_CENTER, wordWrap='CJK')

        # 4) Document + header callback
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=36, rightMargin=36, topMargin=54, bottomMargin=36)

        def draw_header(canvas, doc_):
            y_top = doc_.height + doc_.topMargin + 10
            y = doc_.height + doc_.topMargin + 10
            if logo_path:
                try:
                    # Draw logo (keep it small and left-aligned)
                    canvas.drawImage(logo_path, doc_.leftMargin, y - 30, width=120, height=30, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            # datetime on the right
            qr_size = 60
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            canvas.setFont("Helvetica", 9)
            x_right = doc_.pagesize[0] - doc_.rightMargin
            canvas.drawRightString(x_right, y_top, now_str)
            canvas.setFont("Helvetica-Bold", 14)
            qr_data = f"{id}"
            # Build the QR widget
            qr_widget = qr.QrCodeWidget(qr_data)
            bounds = qr_widget.getBounds()
            w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
            # Choose the QR size in points (72 points = 1 inch)
            # 1 inch square; change to 96/120 for larger
            # Scale the widget to the target size
            d = Drawing(qr_size, qr_size, transform=[qr_size / w, 0, 0, qr_size / h, 0, 0])
            d.add(qr_widget)
            # Coordenadas top-right
            x = doc_.pagesize[0] - doc_.rightMargin - qr_size
            y_qr = y_top - qr_size
            # Dibuja el QR en el canvas
            renderPDF.draw(d, canvas, x, y_qr)
        # 5) Flowables
        story = []
        # Spacer under header
        story.append(Spacer(1, 40))
        story.append(Paragraph(table_name.replace('_', ' ').capitalize(), title_style))
        story.append(Spacer(1, 20))
        # --- Parent record section ---
        parent_data = [
            [Paragraph(str(k.replace('id_','').replace('_', ' ').capitalize() if k!='id_visualizacion' else 'ID'), cell_style), Paragraph(str(v) if v not in (None, "") else "N/A", cell_style)]
            for k, v in record.items()
        ]
        parent_table = Table(parent_data, repeatRows=1, colWidths=[doc.width * 0.32, doc.width * 0.68])
        parent_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F3F5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBFBFD")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(parent_table)
        # --- Related records sections ---
        if relationships:
            story.append(Spacer(1, 16))
            story.append(Paragraph(relationship_table_name.replace('_', ' ').capitalize(), section_title_style))
            story.append(Spacer(1, 16))

            # Determine column order: all skeys, but drop the FK column (since it's the same for all rows)
            # Build table data
            data = [ [Paragraph(str(k.replace('id_','').replace('_', ' ').capitalize() if k!='id_visualizacion' else 'ID'), cell_style) for k in columns_order] ]
            for row in all_related_results:
                data.append([Paragraph(str(k[1]) if k[1] not in (None, "") else "N/A", cell_style) for k in row])
            # Compute reasonable column widths
            num_cols = 1 + len(columns_order)
            col_widths = [doc.width * 0.08] + [ (doc.width * 0.92) / max(1, len(columns_order)) ] * len(columns_order)

            rel_table = Table(data, repeatRows=1, colWidths=col_widths)
            rel_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F3F5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDE1E6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBFBFD")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))

            # Keep section title + table together when possible
            story.append(KeepTogether([rel_table]))
        # 6) Build PDF
        try:
            doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)
        except Exception as e:
            import traceback; traceback.print_exc()
            return None, f"Error al construir PDF: {str(e)}"

        buffer.seek(0)
        return buffer.getvalue(), None                                   
    return handler(id)