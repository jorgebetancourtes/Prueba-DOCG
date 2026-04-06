async function downloadFile(id,type) {
	try {
		// Solicitar la URL firmada
		const response = await fetch("/generate-presigned-url/"+type, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
                'X-CSRFToken': '{{ csrf_token() }}',
			},
			body: JSON.stringify({ id }),
		});
		if (!response.ok) {
			throw new Error("Error al obtener la URL firmada");
		}
		const data = await response.json();
		const presignedUrl = data.presigned_url;
		window.open(presignedUrl, "_blank");
	} catch (error) {
		console.error("Error al descargar el archivo:", error);
		alert("Hubo un error al intentar descargar el archivo. Inténtelo de nuevo.");
	}
}