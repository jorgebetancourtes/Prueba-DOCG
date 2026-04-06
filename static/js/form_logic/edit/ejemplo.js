const cantidad = document.getElementById("cantidad");
cantidad.addEventListener("change", function() {
    let tipo_de_ajuste = document.getElementById("tipo_de_ajuste").value;
    if(tipo_de_ajuste==='Salida'){
        let cantidad_ingresada = document.getElementById("cantidad").value;
        let id_sucursal = document.getElementById("id_sucursal").value;
        let id_producto = document.getElementById("id_producto").value;
        if(id_sucursal==='' || id_producto==='') {
            cantidad.value=null;
            window.dispatchEvent(new CustomEvent('show-warning', {
                detail: 'Favor de ingresar la Sucursal y el producto.'
            }));
            warningAlert.style.display = 'flex';
            warningAlert.style.opacity = '1'; 
            setTimeout(function() {
                warningAlert.style.opacity = '0';  
                setTimeout(function() {
                    warningAlert.style.display = 'none';
                }, 1000);  
            }, 3000);
        }else{
            fetch(`/ajustes_de_inventario/revision_salida/${id_sucursal}/${id_producto}/${cantidad_ingresada}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token() }}',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.message !== "" && data.status==='warning') {
                    cantidad.value=null;
                    window.dispatchEvent(new CustomEvent('show-warning', {
                        detail: data.message   
                    }));
                    warningAlert.style.display = 'flex';
                    warningAlert.style.opacity = '1'; 
                    setTimeout(function() {
                        warningAlert.style.opacity = '0';  
                        setTimeout(function() {
                            warningAlert.style.display = 'none';
                        }, 1000);  
                    }, 3000);
                } 
            })
            .catch(error => console.error("Error:", error));
            }
        }



});