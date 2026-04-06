GPT_PROMPT=''

OMIT_TABLES = [
    'alembic_version',
    'logs_auditoria',
    'archivos',
    'logs_auditoria',
    'relacion_rutas_usuarios',
    'relacion_rutas_roles',
    'rutas',
    'ai_queries',
    'credenciales_de_usuarios'
]

# title format replacements
TITLE_FORMATS = {
    'id_visualizacion':'ID',
    'creacion': 'creación',
    'descripcion': 'descripción',
    'informacion': 'información',
    'categoria': 'categoría',
    'menu': 'menú',
    'telefono': 'teléfono',
    'razon': 'razón',
    'metodo': 'método',
    'transito': 'tránsito',
    'periodico': 'periódico',
    'genero':'género',
    'direccion':'dirección',
    'codigo':'código',
    'contratacion':'contratación',
    'numero':'número',
    'razon':'razón',
    'direccion':'dirección',
    'nomina':'nómina',
    'electronico':'electrónico',
    'ultimo':'último',
    'sesion':'sesión',
    'metodo':'método',
    'comision':'comisión',
    'codigo':'código',
    'actualizacion': 'actualización',
    'ejecucion': 'ejecución',
    'dias':'días',
    'transito': 'tránsito',
    'interaccion':'interacción',
    'interacciones':'interacciones',
    'ultima':'última',
    'region':'región',
    'cotizacion':'cotización',
    'accion':'acción',

    'id_orden_de_compra_id_visualizacion': 'ID Compra',       
    'id_proveedor_nombre': 'ID Proveedor',       
}

# column names for data imports
TABLE_COLUMN_MAPS = {
    'ordenes_de_compra': {
        'Fecha entrega':'fecha_de_entrega',
    }
}

IDS_PREFIXES = {
    # Sistema
    'usuarios': 'USR',
    'credenciales_de_usuarios': 'CRU',
    'logs_auditoria': 'LOG',
    'categorias_de_reportes': 'CAR',
    'reportes': 'REP',
    'roles': 'ROL',
    'aplicaciones': 'APP',
    'rutas': 'RUT',
    'archivos': 'ARC',
    'ai_queries': 'AIQ',
}