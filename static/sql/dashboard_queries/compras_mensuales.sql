select
    TO_CHAR(fecha_orden,'YYYY-MM') as mes_anio,
    productos.nombre as producto,
    sum(prod.importe_total) as importe_total
from productos_en_ordenes_de_compra as prod
left join ordenes_de_compra as orden
    on prod.id_orden_de_compra=orden.id
left join productos
    on prod.id_producto=productos.id
where 
    orden.estatus='Finalizada'
group by 
    TO_CHAR(fecha_orden,'YYYY-MM'),productos.nombre
order by sum(prod.importe_total) desc
