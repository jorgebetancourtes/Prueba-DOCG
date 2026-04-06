function reload_details(id_main_record) {
    fetch(`/dynamic/double_table/reload_details/${main_table_name}/${id_main_record}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}',
        },
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById("details-container");
        container.innerHTML = "";
        console.log(data)
        data.details.forEach(item => {
            const row = document.createElement("div");
            row.className = "flex justify-between items-center text-sm";

            const label = document.createElement("p");
            label.className = "text-gray text-xs mr-3";
            label.innerText = titleFormat(item.key);
            let value = item.value;
            if (money_format_columns.includes(item.key) && !isNaN(value)) {
                value = formatCurrency(item.value);
            } else if (!isNaN(value) && !item.key.includes('telefono') && !item.key.includes('celular') && !item.key.includes('periodo')) {
                value = formatNumber(item.value);
            }
            const value_element = document.createElement("p");
            value_element.className = "text-sm";
            value_element.innerText = value ?? "";

            row.appendChild(label);
            row.appendChild(value_element);
            container.appendChild(row);
        });
    })
    .catch(error => console.error("Error:", error));
}