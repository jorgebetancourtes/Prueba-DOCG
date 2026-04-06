import uuid
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from python.models import db
from python.models.sistema import *

class OrdenesDeCompra(db.Model,BaseMixin,AuditMixin):

    id_proveedor = db.Column(db.UUID, db.ForeignKey("proveedores.id"), nullable=False)

    fecha_orden = db.Column(db.Date, nullable=False)
    fecha_entrega_estimada = db.Column(db.Date) 
    fecha_entrega_real = db.Column(db.Date)  

    subtotal = db.Column(db.Float, nullable=False, default=0.00)
    descuentos = db.Column(db.Float, default=0.00)
    importe_total = db.Column(db.Float, nullable=False, default=0.00)
    notas = db.Column(db.Text)

    estatus = db.Column(db.String(255),default="En revisión") # e.g., En revisión, Aprobada, Recibida,Cancelada

    proveedor = db.relationship("Proveedores", backref="ordenes_de_compra", lazy=True)

class ProductosEnOrdenesDeCompra(db.Model,BaseMixin,AuditMixin):

    id_orden_de_compra = db.Column(db.UUID, db.ForeignKey("ordenes_de_compra.id"), nullable=False) 
    id_producto = db.Column(db.UUID, db.ForeignKey("productos.id"), nullable=False) 

    cantidad_ordenada = db.Column(db.Float, nullable=False, default=0)
    cantidad_recibida = db.Column(db.Float, default=0)
    precio_unitario = db.Column(db.Float, nullable=False, default=0.00)
    subtotal = db.Column(db.Float, nullable=False, default=0.00)
    descuento_porcentaje = db.Column(db.Float, default=0.00)
    importe_total= db.Column(db.Float, default=0.00)
    fecha_entrega_estimada = db.Column(db.Date) 
    notas = db.Column(db.Text) 
    archivo_cotizacion=db.Column(db.String(255))
    estatus = db.Column(db.String(255),default="Pendiente") # e.g., Pendiente, Recibido,Cancelado

    orden_de_compra = db.relationship("OrdenesDeCompra", backref="productos_en_ordenes_de_compra", lazy=True)
    producto = db.relationship("Productos", backref="productos_en_ordenes_de_compra", lazy=True)


class EntregaDeProductosEnOrdenesDeCompra(db.Model,BaseMixin,AuditMixin):

    id_producto_en_orden_de_compra = db.Column(db.UUID, db.ForeignKey("productos_en_ordenes_de_compra.id"), nullable=False) 

    cantidad_recibida = db.Column(db.Float, nullable=False, default=0)
    fecha_entrega = db.Column(db.Date) 
    imagen_verificacion=db.Column(db.String(255))

    producto_en_orden_de_compra = db.relationship("ProductosEnOrdenesDeCompra", backref="entrega_de_productos_en_ordenes_de_compra", lazy=True)


class Inventario(db.Model,BaseMixin,AuditMixin):

    id_producto = db.Column(db.UUID, db.ForeignKey("productos.id"), nullable=False) 

    cantidad = db.Column(db.Float, nullable=False, default=0)

    producto = db.relationship("Productos", backref="inventario", lazy=True)
