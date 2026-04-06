function update_record(record,column) {
    const safeValue = encodeURIComponent(record[column]);
    fetch(`/dynamic/${table_name}/double_table/update/${column}/${record.id}/${safeValue}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message !== "" && data.status==='warning') {
            showAlert(data.message);
        }else if(data.message !== ""){
            showSuccess(data.message);
        }
        reload_tables();
        reload_details(id_main_record);
    })
    .catch(error => console.error("Error:", error));
}