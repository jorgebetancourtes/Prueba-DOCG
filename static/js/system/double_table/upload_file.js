document.addEventListener("change", async function (e) {
    if (!e.target || e.target.type !== "file") return;

    const fileInput = e.target;
    const form = fileInput.closest("form");

    if (!fileInput.files.length) return;

    showLoader();

    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: "POST",
            body: formData,
        });

        // ⚠️ see section #2 below
        const contentType = response.headers.get("content-type");

        if (contentType && contentType.includes("application/json")) {
            const data = await response.json();

            if (data.alert === "success") {
                window.dispatchEvent(new CustomEvent("show-success", {
                    detail: data.message
                }));
            } else {
                window.dispatchEvent(new CustomEvent("show-info", {
                    detail: data.message
                }));
            }
        }

        // Flask redirect → reload page so flashes appear
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

    } catch (err) {
        console.error("Upload error:", err);
        alert("Error al subir el archivo.");
    } finally {
        hideLoader();
        reload_tables();
    }
});
