import uuid
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from python.models import db
from python.models.sistema import *



class Productos(db.Model,BaseMixin,AuditMixin):

    nombre = db.Column(db.String(255), nullable=False)
    unidad_de_medida = db.Column(db.String(50)) 
    codigo_de_barras = db.Column(db.String(255), nullable=True)
    descripcion = db.Column(db.String(500), nullable=True)
    id_archivo_imagen=db.Column(db.String(255))

    estatus = db.Column(db.String(255),default="Activo")

productos_proveedores = db.Table(
    "productos_proveedores",
    db.Column("id_proveedor", UUID(as_uuid=True), db.ForeignKey("proveedores.id")),
    db.Column("id_producto", UUID(as_uuid=True), db.ForeignKey("productos.id"))
)

class Proveedores(db.Model,BaseMixin,AuditMixin):
    nombre = db.Column(db.String(255), nullable=False)
    razon_social = db.Column(db.String(255))
    rfc = db.Column(db.String(20))
    direccion = db.Column(EncryptedColumn(255))
    codigo_postal = db.Column(db.String(20))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(255))

    persona_contacto = db.Column(db.String(255))
    telefono_contacto = db.Column(db.String(50))
    email_contacto = db.Column(db.String(255))
    condiciones_pago = db.Column(db.String(100)) 

    dias_de_entrega = db.Column(db.ARRAY(db.String(100))) 

    sitio_web = db.Column(db.String(255))
    estatus = db.Column(db.String(255),default="Activo")

    id_producto = db.relationship('Productos', secondary=productos_proveedores)
