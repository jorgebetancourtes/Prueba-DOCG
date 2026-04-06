function update_record(record,column) {
    const safeValue = encodeURIComponent(record[column]);
    fetch(`/dynamic/${table_name}/double_table/update/${column}/${record.id}/${safeValue}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message !== "" && data.status==='warning') {
            showAlert(data.message);
            if (data.value!=''){
                record[column] = data.value;  
                const input = document.querySelector(
                    `[data-record-id="${record.id}"][data-column="${column}"]`
                );
                if (input) {
                    input.value = data.value;
                }
            }
        }else if(data.message !== ""){
            showSuccess(data.message);
        }
        reload_table();
        reload_details(id_main_record);
    })
    .catch(error => console.error("Error:", error));
}