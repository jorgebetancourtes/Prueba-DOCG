select
    productos_en_ordenes_de_compra.id,
    cantidad_ordenada,
    descuento_porcentaje,
    productos.nombre,
    precio_unitario,
    subtotal,
    importe_total,
    fecha_entrega_estimada,
    archivos.nombre_del_archivo as archivo_cotizacion,
    productos_en_ordenes_de_compra.fecha_de_creacion
from productos_en_ordenes_de_compra
left join productos
    on productos_en_ordenes_de_compra.id_producto=productos.id
left join archivos
    on archivos.id= uuid(split_part(productos_en_ordenes_de_compra.archivo_cotizacion, '__', 1))::uuid    
where
    id_orden_de_compra= :id_main_record
