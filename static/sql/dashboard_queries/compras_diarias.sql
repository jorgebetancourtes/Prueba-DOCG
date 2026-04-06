select
    TO_CHAR(fecha_orden,'YYYY-MM-DD') as fecha,
    sum(importe_total) as importe_total
from ordenes_de_compra
where 
    estatus='Finalizada'
    and fecha_orden>= :fecha_inicio
    and fecha_orden<= :fecha_fin
group by 
    TO_CHAR(fecha_orden,'YYYY-MM-DD')
