let getRecordRunCount = 0;

document.addEventListener('alpine:init', () => {
    Alpine.store('modalData', {
        record: null,

        getField(key) {
            if (!Array.isArray(this.record)) return null;

            for (const section of this.record) {
                for (const field of section.fields) {
                    if (field.key === key) {
                        return field.value;
                    }
                }
            }
            return null;
        }
    });
});
function redirectActions(url) {
        if (url.includes("delete")) {
            // Para eliminación se confirma y se envía por POST
            if (confirm('¿Quieres eliminar el registro seleccionado?')) {
                const form = document.getElementById('action_buttons');
                form.action = url;
                form.method = "POST";
                form.submit();
            }
        } else if (url.includes("download_pdf")) {
            // Para descargar PDF se utiliza fetch y se procesa la descarga
            fetch(url, { 
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
				    },
                })
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    } else {
                        throw new Error("No se pudo descargar el archivo.");
                    }
                })
                .then(blob => {
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = downloadUrl;
                    a.download = `${url.split("=")[2]}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.location.reload();
                })
                .catch(error => {
                    alert("Error al descargar el archivo: " + error.message);
                });
        } else {
            window.location.href = url;
        }
}

async function openActions(form, recordId,estatus) {
        showLoader();
        //document.getElementById('id_registro').textContent=recordId;
        document.getElementById('estatus').textContent = estatus;

        const updateButton = document.querySelector('button[data-action="actualizar"]');
        const deleteButton = document.querySelector('button[data-action="delete"]');
        const downloadButton = document.querySelector('button[data-action="descargar"]');
        const filesButton = document.querySelector('button[data-action="files"]');

        if (updateButton) {
            updateButton.setAttribute('onclick', `redirectActions('/dynamic/${form}/form?id=${recordId}')`);
        }

        if (deleteButton) {
            deleteButton.setAttribute('onclick', `redirectActions('/dynamic/${form}/delete?id=${recordId}')`);
        }

        if (downloadButton) {
            downloadButton.setAttribute('onclick', `redirectActions('/files/download_pdf?table=${form}&id=${recordId}')`);
        }
        if (filesButton) {
            filesButton.setAttribute('onclick', `redirectActions('/dynamic/${form}/files/${recordId}')`);
        }

        const data = await get_record(form, recordId);
        const popupActions = document.getElementById('modal');
        Alpine.store('modalData').record = data;
        popupActions.classList.remove('hidden');
        hideLoader();

}
function closeActions() {
        const popupActions = document.getElementById('modal');
        const container = document.getElementById('modal_content');
        container.innerHTML = ''; 
        popupActions.classList.add('hidden');
        getRecordRunCount = 0;
}
async function get_record(form, recordId) {
    try {
        getRecordRunCount++;

        const path = `/dynamic/${form}/data/${recordId}`;
        const response = await fetch(path);

        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }

        const data = await response.json();
        const record = data[0]; // array of sections

        const modal_content = document.getElementById('modal_content');
        modal_content.innerHTML = '';

        let tbody_modal_content_relationship = null;
        try {
            const modal_content_relationship = document.getElementById('modal_content_relationship');
            modal_content_relationship.innerHTML = '<tbody></tbody>';
            tbody_modal_content_relationship = modal_content_relationship.querySelector("tbody");
        } catch (error) {}

        document.getElementById("modal_title").textContent = `${titleFormat(form)}`;

        const buttons = document.getElementById("buttons_modal_exits");
        if (getRecordRunCount === 1) {
            buttons.classList.remove("hidden");
        } else {
            buttons.classList.add("hidden");
        }
        // ===============================
        // SECTION LOOP (ORDER PRESERVED)
        // ===============================
        record.forEach(sectionObj => {
            const sectionName = sectionObj.section;
            const fields = sectionObj.fields;

            // ---- Section title ----
            const sectionTitle = document.createElement('h3');
            sectionTitle.textContent = titleFormat(sectionName);
            sectionTitle.style.marginTop = '20px';
            sectionTitle.style.marginBottom = '10px';
            sectionTitle.style.fontWeight = '600';
            modal_content.appendChild(sectionTitle);

            // ---- Table ----
            const table = document.createElement('table');
            table.className = 'w-full border-collapse';

            const tbody = document.createElement('tbody');
            // ===============================
            // FIELD LOOP (ORIGINAL LOGIC)
            // ===============================
            fields.forEach(({ key, value: rawValue }) => {
                let value = rawValue;
                if (money_format_columns.includes(key) && !isNaN(value)) {
                    value = formatCurrency(value);
                } else if (!isNaN(value) && !key.includes('telefono') && !key.includes('celular') && !key.includes('codigo_postal') && !key.includes('periodo')) {
                    value = formatNumber(value);
                }
                if (isDate(value)) {
                    value = date_format(value);
                }

                const tr = document.createElement('tr');
                // ---- Relationships ----
                if (sectionName==='registros_relacionados') {
                    tr.innerHTML = `
                        <td style="white-space:normal;border-bottom:1px solid ; padding:8px;" class="bg-gray/10">
                            ${titleFormat(key)}
                        </td>
                        <td style="white-space:normal;border-bottom:1px solid ; padding:8px;text-align:center;">
                            <button type="submit"
                                
                                class="btn border text-primary border-transparent rounded-md transition-all duration-300 hover:text-white hover:bg-primary bg-primary/10"
                                onclick="window.location.href='${value}'">
                                Ver
                            </button>
                        </td>
                    `;
                } else if (!['id'].includes(key)) {
                    // ---- File ----
                    if (key in file_columns || key.includes('archivo')) {
                        const [uuid, name] = value.split("__");
                        tr.innerHTML = `
                            <td style="white-space:normal;border-right:1px solid padding:8px;" class="bg-gray/10">
                                ${titleFormat(key)}
                            </td>
                            <td class="clickable-td"
                                style="white-space:normal;border-bottom:1px solid ; padding:8px;">
                                <a href="#"
                                   style="display:block; width:100%; height:100%; text-decoration:none; color:inherit;"
                                   onclick="downloadFile('${uuid}','view')">
                                    ${name}
                                </a>
                            </td>
                        `;
                    }

                    // ---- FK link ----
                    else if (typeof value === 'string' && value.includes('__')) {
                        const [before, id, table_name] = value.split("__");
                        tr.innerHTML = `
                            <td style="white-space:normal;border-bottom:1px solid ; padding:8px;" class="bg-gray/10">
                                ${titleFormat(key)}
                            </td>
                            <td class="clickable-td"
                                style="white-space:normal;border-bottom:1px solid ; padding:8px;">
                                <a href="#"
                                   style="display:block; width:100%; height:100%; text-decoration:none; color:inherit;"
                                   onclick="openActions('${table_name}', '${id}', '')">
                                    ${before}
                                </a>
                            </td>
                        `;
                    }

                    // ---- Normal value ----
                    else {
                        tr.innerHTML = `
                            <td style="white-space:normal;border-bottom:1px solid ; padding:8px;" class="bg-gray/10">
                                ${titleFormat(key)}
                            </td>
                            <td style="white-space:normal;border-bottom:1px solid ; padding:8px;">
                                ${value}
                            </td>
                        `;
                    }
                }
                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            modal_content.appendChild(table);
        });

        return record;

    } catch (error) {
        console.error("Error fetching or processing data:", error);
        return null;
    }
}


document.addEventListener('keydown', function (event) {
    // If ESC key is pressed
    if (event.key === "Escape") {
        closeActions();
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    const search = window.location.search;
    const match = search.match(/[?&]open_modal(?:=|%3D)([^&]*)/i);

    if (match && match[1]) {
        try {
            // match[1] is the raw value (possibly URL-encoded)
            let openModal = decodeURIComponent(match[1]);
            // In some weird cases you might still get "=123" or "3D123"
            openModal = openModal.replace(/^(=|3D)/i, "").trim();
            await openActions(table_name, openModal, "");
        } catch (err) {
            console.error("Error auto-opening modal:", err);
        }
    }
});