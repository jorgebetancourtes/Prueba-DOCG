    (
        function fillInputsFromUrl() {
        const params = new URLSearchParams(window.location.search);

        params.forEach((value, key) => {
            const input = document.querySelector(`[name="${key}"]`);
            if (input) {
            input.value = value;
            }
        });
    })();

    document.addEventListener("DOMContentLoaded", function () {
        const params = new URLSearchParams(window.location.search);

        params.forEach((value, key) => {
            let field = document.querySelector(`[name="${key}"]`);
            if (!field) return;

            if (field.tagName === "SELECT") {
                if (field.multiple) {
                    let values = value.split(",");
                    for (let opt of field.options) {
                        if (values.includes(opt.textContent.trim())) {
                            opt.selected = true;
                        }
                    }
                } else {
                    for (let opt of field.options) {
                        if (opt.textContent.trim() === value) {
                            opt.selected = true;
                            break;
                        }
                    }
                }
                $(field).trigger('change'); // Refresh Select2 UI if applied

            } else if (field.type === "checkbox" || field.type === "radio") {
                field.checked = (field.value === value);
            } else {
                field.value = value;
            }
        });
    });