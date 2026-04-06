select
    id_visualizacion,
    importe_total
from ordenes_de_compra
where 
    estatus='Finalizada'
