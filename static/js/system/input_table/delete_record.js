async function deleteRecord(tableName, modelSecondTable, mainId, recordId, csrfToken) {
    showLoader();
    fetch(`/dynamic/${tableName}/double_table/delete/${modelSecondTable}/${mainId}/${recordId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message !== "" && data.status==='warning') {
            showAlert(data.message);
        }
        reload_table();
        reload_details(id_main_record);        
    })
    .catch(error => console.error("Error:", error));    
}