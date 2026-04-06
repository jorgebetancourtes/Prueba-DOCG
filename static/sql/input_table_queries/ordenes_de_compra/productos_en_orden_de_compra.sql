with cantidad_anterior as (
    select
        entrega.id_producto_en_orden_de_compra,
        coalesce(sum(entrega.cantidad_recibida),0) as cantidad_recibida_anteriormente
    from entrega_de_productos_en_ordenes_de_compra as entrega
    left join productos_en_ordenes_de_compra as prod
        on entrega.id_producto_en_orden_de_compra=prod.id
    where
        prod.id_orden_de_compra = :id_main_record
    group by 
        entrega.id_producto_en_orden_de_compra
)
select
    productos_en_ordenes_de_compra.id,
    cantidad_ordenada,
    case when cantidad_recibida=Null then coalesce(cantidad_ordenada-cantidad_recibida_anteriormente,cantidad_ordenada) else cantidad_recibida  end as cantidad_recibida,
    coalesce(cantidad_recibida_anteriormente,0) as cantidad_recibida_anteriormente,
    nombre,
    coalesce(notas,'') as notas,
    productos_en_ordenes_de_compra.fecha_de_creacion
from productos_en_ordenes_de_compra
left join productos
    on productos_en_ordenes_de_compra.id_producto=productos.id
left join cantidad_anterior
    on cantidad_anterior.id_producto_en_orden_de_compra=productos_en_ordenes_de_compra.id 
where
    id_orden_de_compra = :id_main_record
    and  coalesce(cantidad_ordenada-cantidad_recibida_anteriormente,cantidad_ordenada)>0
