select
    count(id) as indicador
from viajes
where estatus!='Cancelado'
and id_integrante=:id_integrante