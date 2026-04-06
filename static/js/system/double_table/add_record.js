async function addRecord(tableName,modelFirstTable, modelSecondTable, mainId, recordId, csrfToken) {
    showLoader();
    const url = `/dynamic/${tableName}/double_table/add/${modelFirstTable}/${modelSecondTable}/${mainId}/${recordId}`;
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({}) // you can send extra data if needed
        });

        if (response.ok) {
            reload_tables();
            reload_details(id_main_record);
        } else {
            showDanger("Error al eliminar el reigstro.");
        }
    } catch (error) {
        showDanger('Error al eliminar el registro');
    }
}