function titleFormat(value) {
  const replacements = title_formats;
  // Check for exact match
  if (replacements[value]) {
    return replacements[value].charAt(0).toUpperCase() + replacements[value].slice(1);
  }

  // Replace underscores with spaces
  let formatted = value.replace(/_/g, " ");
  // Remove "id " prefix if present
  if (formatted.startsWith("id ")) {
    formatted = formatted.slice(3);
  }

  // Replace words with accented versions if needed
  for (let k in replacements) {
    const regex = new RegExp(`\\b${k}\\b`, "i");
    if (regex.test(formatted)) {
      formatted = formatted.replace(regex, replacements[k]);
    }
  }
  formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1);

  return formatted;
}
// funcion para obtener el lunes de hace dos semanas
function getMondayOfTwoWeeksAgo() {
    const today = new Date();
    // Subtract 14 days (2 weeks)
    const twoWeeksAgo = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);
    // Get the day of week (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
    const day = twoWeeksAgo.getDay();
    // Calculate difference to get to Monday (if Sunday, go back 6 days; else, go back (day-1) days)
    const diffToMonday = day === 0 ? -6 : 1 - day;
    const monday = new Date(twoWeeksAgo);
    monday.setDate(twoWeeksAgo.getDate() + diffToMonday);
    // Return as YYYY-MM-DD
    return monday.toISOString().split('T')[0];
}
function money_format(value) {
    return `$${new Intl.NumberFormat().format(value)}`;
}
function formatNumber(value) {
        // Format number with commas as thousands separators
        return new Intl.NumberFormat('en-US').format(value);
}
function formatCurrency(value) {
        // Ensure it's a valid number, then format it as currency
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}
// funcion para obtener un valor de un sql
function obtener_valor(selector,columnName,path,format) {
    return fetch(path)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        document.querySelector(selector).textContent=''
        if (format === 'currency') {
            document.querySelector(selector).textContent = money_format(data[0][columnName]);
        } else if (format === 'percent') {
            let val = data[0][columnName];
            if (val !== null && val !== undefined) {
                val=Number(val)
                document.querySelector(selector).textContent = val.toFixed(0) + '%';
            }
        } else {
            document.querySelector(selector).textContent = data[0][columnName];
        }
    })
    .catch(error => {
        console.error("Error fetching or processing data:", error);
    });
}
function render_dynamic_table(element_id, path) {
    fetch(path)
        .then(response => {
            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
            return response.json();
        })
        .then(payload => {
            const { columns, data } = payload;

            const container = document.getElementById(element_id);

            if (!data || data.length === 0) {
                container.innerHTML = "<p class='text-gray-500 italic'>No data available</p>";
                return;
            }

            let html = `
                <table class="table-striped">
                    <thead class="text-left bg-white dark:bg-dark sticky top-0 z-5">
                        <tr class="text-center">
                            ${columns.map(col => `<th>${titleFormat(col)}</th>`).join("")}
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.forEach(row => {
                html += `<tr>`;

                columns.forEach(col => {
                    let value = row[col];

                    if (money_format_columns.includes(col) && !isNaN(value)) {
                        value = formatCurrency(value);
                    } else if (!isNaN(value) && 
                               !col.includes("telefono") && 
                               !col.includes("celular") && 
                               !col.includes("periodo")) {
                        value = formatNumber(value);
                    }

                    html += `<td style="white-space: normal">${value ?? ""}</td>`;
                });

                html += `</tr>`;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        })
        .catch(err => {
            console.error("Error fetching or processing data:", err);
            document.getElementById(element_id).innerHTML =
                "<p class='text-red-500 italic'>Error loading data</p>";
        });
}
