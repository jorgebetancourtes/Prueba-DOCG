
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for,session

from python.models import db
from python.models.modelos import *
from python.services.system.authentication import *
from sqlalchemy.orm import joinedload
from sqlalchemy import String, Text, or_,func,desc
from datetime import date,timedelta
from python.services.system.helper_functions import *

ordenes_de_compra_bp = Blueprint("ordenes_de_compra", __name__,url_prefix="/ordenes_de_compra")

@ordenes_de_compra_bp.route("/aprobar/<id>", methods=["GET","POST"])
@login_required
@roles_required()
@return_url_redirect
def aprobar(id):
    try:
        record=OrdenesDeCompra.query.get(id)
        if record.estatus=='En revisión':
            record.estatus="Aprobada"
            record.subtotal=(
                    db.session.query(
                        func.sum(ProductosEnOrdenesDeCompra.subtotal)
                    )
                    .filter(ProductosEnOrdenesDeCompra.id_orden_de_compra == record.id)
                    .scalar()
                    or 0  
                )
            record.importe_total=(
                    db.session.query(
                        func.sum(ProductosEnOrdenesDeCompra.importe_total)
                    )
                    .filter(ProductosEnOrdenesDeCompra.id_orden_de_compra == record.id)
                    .scalar()
                    or 0  
                )
            record.descuentos=abs(record.importe_total-record.subtotal)
            db.session.commit()
            flash('La orden de compra ha sido Aprobada.','success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al aprobar la orden de compra: {str(e)}", "danger")
    return redirect(url_for('dynamic.table_view', table_name='ordenes_de_compra'))

@ordenes_de_compra_bp.route("/cancelar/<id>", methods=["GET","POST"])
@login_required
@roles_required()
@return_url_redirect
def cancelar(id):
    try:
        record=OrdenesDeCompra.query.get(id)
        if record.estatus in ('En revisión','Aprobada') and record.estatus_pago=='Sin pagar':
            record.estatus="Cancelada"
            productos=ProductosEnOrdenesDeCompra.query.filter_by(id_orden_de_compra=id)
            for prod in productos:
                prod.estatus="Cancelado"
            record.subtotal=0
            record.descuentos=0
            record.importe_total=0
            db.session.commit()
            flash('La orden de compra ha sido Cancelada.','success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al cancelar la orden de compra: {str(e)}", "danger")
    return redirect(url_for('dynamic.table_view', table_name='ordenes_de_compra'))

@ordenes_de_compra_bp.route("/recibir/<id>", methods=["GET"])
@login_required
@roles_required()
@return_url_redirect
def recibir(id):
    record=OrdenesDeCompra.query.get(id)
    if record.estatus in ('Aprobada','Recibida parcial'):
        return redirect(url_for('dynamic.table_view_input', main_table_name='ordenes_de_compra',id=id))

@ordenes_de_compra_bp.route("/confirmar/<id>", methods=["GET"])
@login_required
@roles_required()
@return_url_redirect
def confirmar(id):
    try:
        record=OrdenesDeCompra.query.get(id)
        if record.estatus in ('Aprobada','Recibida parcial'):
            cantidad_total_recibida=(
                db.session.query(
                    func.sum(ProductosEnOrdenesDeCompra.cantidad_recibida)
                )
                .filter(ProductosEnOrdenesDeCompra.id_orden_de_compra == record.id)
                .scalar()
                or 0  
            )
            if cantidad_total_recibida>0:
                record.estatus="Recibida"
                productos=ProductosEnOrdenesDeCompra.query.filter_by(id_orden_de_compra=id)
                for prod in productos:
                    if prod.estatus!='Cancelado':
                        cantidad_recibida_anteriormente=(
                                db.session.query(
                                    func.sum(EntregaDeProductosEnOrdenesDeCompra.cantidad_recibida)
                                )
                                .filter(EntregaDeProductosEnOrdenesDeCompra.id_producto_en_orden_de_compra == prod.id)
                                .scalar()
                                or 0  
                            )
                        cantidad_recibida_total=cantidad_recibida_anteriormente+prod.cantidad_recibida
                        if prod.cantidad_ordenada==cantidad_recibida_total:
                            prod.estatus='Recibido'
                        elif prod.cantidad_ordenada>cantidad_recibida_total:
                            prod.estatus="Recibido parcial"
                            record.estatus="Recibida parcial"
                        # crear registro de entrega
                        new_record=EntregaDeProductosEnOrdenesDeCompra(
                                id_producto_en_orden_de_compra=prod.id,
                                cantidad_recibida=prod.cantidad_recibida,
                                fecha_entrega=datetime.today(),
                                id_usuario=session['id_usuario']
                        )
                        db.session.add(new_record)
                        prod.cantidad_recibida=cantidad_recibida_total
                db.session.commit()
                flash('La orden de compra ha sido Recibida.','success')
            else:
                flash('Los productos de la orden de compra deben de tener una cantidad recibida mayor a 0.','warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al confirmar la orden de compra: {str(e)}", "danger")
    return redirect(url_for('dynamic.table_view', table_name='ordenes_de_compra'))

@ordenes_de_compra_bp.route("/finalizar/<id>", methods=["GET","POST"])
@login_required
@roles_required()
def finalizar(id):
    try:
        record=OrdenesDeCompra.query.get(id)
        if record.estatus in ('Recibida parcial','Recibida'):
            session['return_url']=request.args.get("return_url", "")
            return redirect(url_for('dynamic.form', table_name='ordenes_de_compra',id=id,accion='Finalizar'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al finalizar la orden de compra: {str(e)}", "danger")
    return redirect(url_for('dynamic.table_view', table_name='ordenes_de_compra'))


'''
@ordenes_de_compra_bp.route("/finalizar/<id>", methods=["GET","POST"])
@login_required
@roles_required()
@return_url_redirect
def finalizar(id):
    try:
        record=OrdenesDeCompra.query.get(id)
        if record.estatus in ('Recibida parcial','Recibida'):
            record.estatus="Finalizada"
            productos=ProductosEnOrdenesDeCompra.query.filter_by(id_orden_de_compra=id)
            subtotal=0
            descuento=0
            for prod in productos:
                subtotal_prod=prod.cantidad_recibida*prod.precio_unitario
                prod.subtotal=subtotal_prod*(1-prod.descuento_porcentaje/100)
                subtotal=subtotal+subtotal_prod
                descuento=descuento+prod.cantidad_recibida*prod.precio_unitario*prod.descuento_porcentaje/100
            record.subtotal=subtotal
            record.descuentos=descuento
            record.importe_total=subtotal-descuento
            db.session.commit()
            flash('La orden de compra ha sido Finalizada.','success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al finalizar la orden de compra: {str(e)}", "danger")
    return redirect(url_for('dynamic.table_view', table_name='ordenes_de_compra'))
'''
'''
# CHECKBOX ACTIONS
@ordenes_de_compra_bp.route("/aprobar", methods=["POST"])
@login_required
@csrf.exempt
def aprobar():
    try:
        data = request.get_json()
        ids = data.get("ids", [])
        # One single database query
        result = (
            Noticias.query
            .filter(Noticias.id.in_(ids), Noticias.estatus == "Sin revisar")
            .update({ "estatus": "Aprobada" }, synchronize_session=False)
        )
        db.session.commit()
        return jsonify({"success": True, "message": f"Se han revisado {result} noticias."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"danger": True, "message": f"Error al revisar: {str(e)}"}), 500

'''