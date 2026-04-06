from datetime import timedelta
from python.services.system.helper_functions import *
from python.models.modelos import *
from sqlalchemy import or_, and_, func

###############
#  Table View Input
###################

def get_variables_table_view_input(table_name):
    columns = {
        "ordenes_de_compra": {
            "columns":["nombre","cantidad_ordenada","cantidad_recibida_anteriormente","cantidad_recibida","notas"],
            "table_title":"Productos en orden de compra",
            "query_table":"productos_en_orden_de_compra",
            "table_name":"productos_en_ordenes_de_compra",
            "edit_fields":['cantidad_recibida','notas'],
            "required_fields":['cantidad_recibida'],
            "details":["id_visualizacion","proveedor",'importe_total'],            
            "url_confirm":"ordenes_de_compra.confirmar",
            'delete_button':'si',
            'add_button':'si'
        },
    }
    columns=columns.get(table_name,'')
    return columns

###################
#  Both
###################

def get_update_validation(table_name,record,column,value):
    validation={}
    validation['status']=1
    validation['value_warning']=''
    if table_name=='productos_en_ordenes_de_compra' and column in ('cantidad_ordenada','descuento_porcentaje','precio_unitario','subtotal'):
        if column=='cantidad_ordenada':
            record.subtotal=float(value)*record.precio_unitario
            record.importe_total=record.subtotal*(100-record.descuento_porcentaje)/100   
        elif column=='descuento_porcentaje':
            if float(value)>100:
                validation['status']=0
                validation['message']="El descuento no puede ser mayor a 100%"
                validation['value_warning']=''
                return validation
            record.importe_total=record.subtotal*(100-float(value))/100     
        elif column=='precio_unitario':
            record.subtotal=float(value)*record.cantidad_ordenada
            record.importe_total=record.subtotal*(100-record.descuento_porcentaje)/100   
        elif column=='subtotal':
            record.precio_unitario=float(value)/record.cantidad_ordenada
            record.importe_total=float(value)*(100-record.descuento_porcentaje)/100               
        orden=OrdenesDeCompra.query.get(record.id_orden_de_compra)
        orden.subtotal=(
                db.session.query(
                    func.sum(ProductosEnOrdenesDeCompra.subtotal)
                )
                .filter(ProductosEnOrdenesDeCompra.id_orden_de_compra == orden.id)
                .scalar()
                or 0  
            )
        orden.importe_total=(
                db.session.query(
                    func.sum(ProductosEnOrdenesDeCompra.importe_total)
                )
                .filter(ProductosEnOrdenesDeCompra.id_orden_de_compra == orden.id)
                .scalar()
                or 0  
            )
        orden.descuentos=abs(record.importe_total-record.subtotal)
        validation['status']=1
    elif table_name=='productos_en_ordenes_de_compra' and column=='cantidad_recibida':
        cantidad_recibida_anteriormente=(
                db.session.query(
                    func.sum(EntregaDeProductosEnOrdenesDeCompra.cantidad_recibida)
                )
                .filter(EntregaDeProductosEnOrdenesDeCompra.id_producto_en_orden_de_compra == record.id)
                .scalar()
                or 0  
            )
        cantidad_restante=record.cantidad_ordenada-cantidad_recibida_anteriormente
        if float(value)>cantidad_restante:
            validation['status']=0
            validation['message']="La cantidad recibida no puede ser mayor a la cantidad restante por entregar."
            validation['value_warning']=cantidad_restante  
    return validation
