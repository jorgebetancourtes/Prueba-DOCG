select
    sum(importe_total) as importe_total
from ordenes_de_compra
where 
    estatus='Finalizada'
