// static/js/generate_excel.js

function generate_excel(table,kind) {
    const baseUrl = `/files/excel/${kind}/${table}`;
    const currentParams = window.location.search; // includes the "?" if present
    const url = currentParams ? `${baseUrl}${currentParams}` : baseUrl;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error("Error al generar el archivo Excel");
            }
            return response.blob();
        })
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = downloadUrl;
            a.download = `${titleFormat(table_name)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            message='Se ha descargado el archivo exitosamente.'
            window.dispatchEvent(new CustomEvent('show-success', { detail: message}));
        })
        .catch(error => {
            console.error("Error:", error);
            alert("No se pudo generar el archivo Excel.");
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("file-upload");
    const form = document.getElementById("dynamic_form");

    fileInput.addEventListener("change", async function () {
        if (!fileInput.files.length) return;
        showLoader();
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (data.alert == 'success') {
                window.dispatchEvent(new CustomEvent('show-success', {
                    detail: data.message
                }));
                successAlert.style.display = 'flex';
                successAlert.style.opacity = '1';
                setTimeout(function () {
                    successAlert.style.opacity = '0';
                    setTimeout(function () {
                    successAlert.style.display = 'none';
                    }, 1000);
                }, 3000);
            } else {
                window.dispatchEvent(new CustomEvent('show-info', {
                    detail: data.message
                }));
                infoAlert.style.display = 'flex';
                infoAlert.style.opacity = '1';
                setTimeout(function () {
                    infoAlert.style.opacity = '0';
                    setTimeout(function () {
                    infoAlert.style.display = 'none';
                    }, 1000);
                }, 3000);
            }            
            // Redirect on success/failure to allow Flask flash messages to appear
            if (response.redirected) {
                window.location.href = response.url;  // show flash messages
                return;
            }
        } catch (err) {
            console.error("Upload error:", err);
            alert("Error al subir el archivo.");
        }
        reload_table();
        hideLoader();
    });
});