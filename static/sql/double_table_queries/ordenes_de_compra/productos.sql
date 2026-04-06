with productos_seleccionados as (
    select
        id_producto
    from productos_en_ordenes_de_compra
    where 
        id_orden_de_compra=:id_main_record
)
select
    productos.id,
    productos.nombre,
    productos.fecha_de_creacion
from productos
where
    productos.estatus='Activo'
    AND NOT EXISTS (
      SELECT 1
      FROM productos_seleccionados ps
      WHERE ps.id_producto = productos.id
    )