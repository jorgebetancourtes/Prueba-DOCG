
from python.models.modelos import *
from sqlalchemy import String, Text, or_,func,Integer, Float, Numeric
from sqlalchemy.sql import case
from flask import session,flash,request
from datetime import date, datetime,timedelta
from decimal import Decimal

#####
# funciones auxiliares para hacer calculos generales
#####

def get_all_models():
    """
    Retorna una lista de todos los modelos registrados en SQLAlchemy
    que tienen asignado el atributo __tablename__.
    """
    models = []
    for model in db.Model.registry._class_registry.values():
        if hasattr(model, "__tablename__"):
            models.append(model)
    return models

def cuadrar_balance(id_cuenta):
    cuenta=CuentasDeBanco.query.get(id_cuenta)
    pagos=(db.session.query(func.sum(Pagos.importe)).filter(Pagos.id_cuenta_de_banco == cuenta.id,Pagos.estatus=='Pagado').scalar() or 0)
    ingresos=(db.session.query(func.sum(Ingresos.importe)).filter(Ingresos.id_cuenta_de_banco == cuenta.id,Ingresos.estatus=='Cerrado').scalar() or 0)
    transferencia_salida=(db.session.query(func.sum(TransferenciasDeDinero.importe)).filter(TransferenciasDeDinero.id_cuenta_de_banco_salida == cuenta.id,TransferenciasDeDinero.estatus=='Realizada').scalar() or 0)
    transferencia_entrada = (db.session.query(func.sum(TransferenciasDeDinero.importe)).filter(TransferenciasDeDinero.id_cuenta_de_banco_entrada == cuenta.id,TransferenciasDeDinero.estatus == 'Realizada').scalar()or 0)
    ajustes_salida = (db.session.query(func.sum(AjustesDeDinero.importe)).filter(AjustesDeDinero.id_cuenta_de_banco == cuenta.id,AjustesDeDinero.estatus == 'Realizado',AjustesDeDinero.tipo_de_ajuste == 'Salida').scalar()or 0)
    ajustes_entrada = (db.session.query(func.sum(AjustesDeDinero.importe)).filter(AjustesDeDinero.id_cuenta_de_banco == cuenta.id,AjustesDeDinero.estatus == 'Realizado',AjustesDeDinero.tipo_de_ajuste == 'Entrada').scalar()or 0)

    cuenta.balance=ingresos+transferencia_entrada+ajustes_entrada-pagos-transferencia_salida-ajustes_salida

def calcular_importe_pago(record):
    record.importe=(db.session.query(func.sum(GastosEnPagos.importe)).filter(GastosEnPagos.id_pago == record.id).scalar() or 0)
    gastos=Gastos.query.filter(Gastos.id_proveedor==record.id_proveedor,Gastos.estatus!='Pagado',Gastos.estatus!='Cancelado').all()
    for gasto in gastos:
        gasto.importe_pagado=(db.session.query(func.sum(GastosEnPagos.importe)).join(Pagos, GastosEnPagos.id_pago == Pagos.id).filter(GastosEnPagos.id_gasto == gasto.id).filter(Pagos.estatus != "Cancelado").scalar()) or 0


def calcular_importe_factura(record):
    record.subtotal=(db.session.query(func.sum(ServiciosEnFacturas.importe)).filter(ServiciosEnFacturas.id_factura == record.id).scalar() or 0)    
    record.impuestos=(db.session.query(func.sum(ServiciosEnFacturas.impuesto)).filter(ServiciosEnFacturas.id_factura == record.id).scalar() or 0)    
    record.importe_total=record.subtotal+record.impuestos

def calcular_importe_ingreso(record):
    facturas=Facturas.query.filter(Facturas.id_cliente==record.id_cliente,Facturas.estatus!='Cobrada',Facturas.estatus!='Cancelada').all()
    for factura in facturas:
        factura.importe_cobrado=(db.session.query(func.sum(FacturasEnIngresos.importe)).join(Ingresos, FacturasEnIngresos.id_ingreso == Ingresos.id).filter(FacturasEnIngresos.id_factura == factura.id).filter(Ingresos.estatus != "Cancelado").scalar()) or 0

           
