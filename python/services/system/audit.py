# python/models/logs_auditoria.py

from datetime import date, datetime

from flask import g

from python.models import db
from python.models.modelos import *


def get_models_audit():
    models = []
    for model in db.Model.registry._class_registry.values():
        if hasattr(model, "__tablename__") and model.__name__ != "LogsAuditoria" and model.__name__ != "Usuarios":
            models.append(model)
    return tuple(models)

def clear_audit_flag(session):
    session._audit_logged = False
    session._audit_created_logged = False
    
def add_logs_audit(session, flush_context, instances):
    if getattr(session, "_audit_logged", False):
        return  # Ya se ejecutó
    session._audit_logged = True
    """add logs de auditoría para las operaciones en la base de datos."""
    import json
    from datetime import date, datetime

    def serialize_value(value):
        """Convierte valores a formatos serializables por JSON."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return None
        elif isinstance(value, (int, float, str, dict, list)):
            return value
        return str(value)

    logs = []

    # loggear registros modificados
    models_audit=get_models_audit()
    for instance in session.dirty:
        if isinstance(instance, models_audit):
            state = db.inspect(instance)
            original = {}
            modified = {}

            for attr in state.attrs:
                if attr.history.has_changes():
                    original[attr.key] = (
                        serialize_value(attr.history.deleted[0])
                        if attr.history.deleted
                        else None
                    )
                    modified[attr.key] = (
                        serialize_value(attr.history.added[0])
                        if attr.history.added
                        else None
                    )

            if original or modified:
                log = LogsAuditoria(
                    tabla=instance.__tablename__,
                    id_registro=getattr(instance, "id", None),
                    usuario=g.usuario_email if hasattr(g, "usuario_email") else "Desconocido",
                    accion="Actualización",
                    datos_anteriores=json.dumps(original, ensure_ascii=False),
                    datos_nuevos=json.dumps(modified, ensure_ascii=False),
                    fecha=datetime.utcnow(),
                )
                logs.append(log)

    # loggear registros eliminados
    models_audit=get_models_audit()
    for instance in session.deleted:
        if isinstance(instance, models_audit):
            original = {
                column.name: serialize_value(getattr(instance, column.name))
                for column in instance.__table__.columns
            }

            log = LogsAuditoria(
                tabla=instance.__tablename__,
                id_registro=getattr(instance, "id", None),
                usuario=g.usuario_email
                if hasattr(g, "usuario_email")
                else "Desconocido",
                accion="Eliminación",
                datos_anteriores=json.dumps(original, ensure_ascii=False),
                datos_nuevos=None,
                fecha=datetime.utcnow(),
            )
            logs.append(log)

    # Agregar los logs de modificaciones y eliminaciones
    if logs:
        session.add_all(logs)


def add_logs_post_flush(session, flush_context):
    if getattr(session, "_audit_created_logged", False):
        return 
    session._audit_created_logged = True
    """add logs de auditoría después de que se asignen los IDs."""
    import json

    from flask import g

    def serialize_value(value):
        """Convierte valores a formatos serializables por JSON."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return None
        elif isinstance(value, (int, float, str, dict, list)):
            return value
        return str(value)

    logs = []

    # loggear registros creados
    models_audit=get_models_audit()
    for instance in session.new:
        if isinstance(instance, models_audit):
            nuevos_datos = {
                column.name: serialize_value(getattr(instance, column.name))
                for column in instance.__table__.columns
            }

            log = LogsAuditoria(
                tabla=instance.__tablename__,
                id_registro=getattr(instance, "id", None),
                usuario=g.usuario_email
                if hasattr(g, "usuario_email")
                else "Desconocido",
                accion="Creación",
                datos_anteriores=None,
                datos_nuevos=json.dumps(nuevos_datos, ensure_ascii=False),
                fecha=datetime.utcnow(),
            )
            logs.append(log)

    if logs:
        session.add_all(logs)
