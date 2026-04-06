    document.getElementById("file-upload")?.addEventListener("change", function () {
        const fileNameSpan = document.getElementById("file-name");
        if (!fileNameSpan) return;

        fileNameSpan.textContent =
            this.files[0]?.name || "No se ha seleccionado ningún archivo";
    });

    document.getElementById("delete-file-btn")?.addEventListener("click", function () {
        const fileInput = document.getElementById("file-upload");
        const fileNameSpan = document.getElementById("file-name");

        if (!fileInput || !fileNameSpan) return;

        fileInput.value = "";
        fileNameSpan.textContent = "No se ha seleccionado ningún archivo";
    });

    document.addEventListener("change", function (e) {
        if (!e.target || !e.target.matches("[data-file-input]")) return;

        const wrapper = e.target.closest("[data-file-widget]");
        if (!wrapper) return;

        const fileNameSpan = wrapper.querySelector("[data-file-name]");
        const fileName = e.target.files[0]?.name || "No se ha seleccionado ningún archivo";

        fileNameSpan.textContent = fileName;
    });
    document.addEventListener("click", function (e) {
        if (!e.target.closest("[data-delete-file]")) return;

        const wrapper = e.target.closest("[data-file-widget]");
        if (!wrapper) return;

        const fileInput = wrapper.querySelector("[data-file-input]");
        const fileNameSpan = wrapper.querySelector("[data-file-name]");

        if (fileInput) fileInput.value = "";
        if (fileNameSpan) fileNameSpan.textContent = "No se ha seleccionado ningún archivo";
    });