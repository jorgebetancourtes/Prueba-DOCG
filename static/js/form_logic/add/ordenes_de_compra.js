document.getElementById("dynamic_form").addEventListener("submit", async function (e) {
  e.preventDefault(); // Stop form submission until we check
    const fecha_inicio = new Date(document.getElementById("fecha_orden").value);
    const fecha_fin = new Date(document.getElementById("fecha_entrega_estimada").value);
    if(fecha_inicio>fecha_fin){
		showAlert('La fecha de orden no puede ser mayor a la fecha entrega.');
    }else{
      	e.target.submit();
    }
});
