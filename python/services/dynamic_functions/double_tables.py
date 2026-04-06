from datetime import timedelta
from python.services.system.helper_functions import *
from python.models.modelos import *
from sqlalchemy import or_, and_, func

###############
#  Duuble Table View 
###################

def get_variables_double_table_view(table_name):
    columns = {
        "ordenes_de_compra": {
            "columns_first_table":["nombre"],
            "columns_second_table":["nombre","cantidad_ordenada","precio_unitario","subtotal","descuento_porcentaje","importe_total","fecha_entrega_estimada","archivo_cotizacion"],
            "title_first_table":"Productos",
            "title_second_table":"Productos en orden de compra",
            "query_first_table":"productos",
            "query_second_table":"productos_en_orden_de_compra",
            "model_first_table":"productos",
            "model_second_table":"productos_en_ordenes_de_compra",
            "edit_fields":['precio_unitario','cantidad_ordenada','descuento_porcentaje','subtotal','fecha_entrega_estimada'],
            "required_fields":['precio_unitario','cantidad_ordenada','descuento_porcentaje','subtotal','fecha_entrega_estimada'],
            "details":["id_visualizacion","proveedor.nombre",'importe_total'],
            "url_confirm":"ordenes_de_compra.confirmar"            
        },
    }
    columns=columns.get(table_name,'')
    return columns

def add_record_double_table(main_table_name,second_table,id_main_record,id_record):
    model=get_model_by_name(second_table)
    if main_table_name=='ordenes_de_compra':
        orden=OrdenesDeCompra.query.get(id_main_record)
        new_record=model(
            id_orden_de_compra=id_main_record,
            id_producto=id_record,
            precio_unitario=0,
            cantidad_ordenada=0,
            cantidad_recibida=0,
            descuento_porcentaje=0,
            subtotal=0,
            fecha_entrega_estimada=orden.fecha_entrega_estimada,
            id_usuario=session['id_usuario']
        )
    return new_record

def validate_delete(table_name,id):
    if table_name=='table_name':
        record=table_name.query.get(id)
        if record.column=='':
            return False
    return True

def on_add_double_table(table_name,id):
    if table_name=='ejemplo':
        orden=OrdenesDeVenta.query.get(id)


def on_update_double_table(table_name,id):
    if table_name=='ejemplo':
        orden=OrdenesDeVenta.query.get(id)

def on_delete_double_table(table_name,id):
    if table_name=='ejemplo':
        orden=OrdenesDeVenta.query.get(id)
