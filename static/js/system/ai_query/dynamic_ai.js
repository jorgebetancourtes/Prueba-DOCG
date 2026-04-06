function fillQuestion(data) {
    document.getElementById("question_text").innerText = data.question;
    document.getElementById("question_wrapper").classList.remove("hidden");
}

function fillAnswer(data) {
    document.getElementById("answer_wrapper").classList.remove("hidden");

    if (data.answer_html) {
        document.getElementById("answer_html").innerHTML = data.answer_html;
        document.getElementById("answer_html").classList.remove("hidden");
        document.getElementById("aiModalContent").innerHTML = data.answer_html;        
    } else {
        document.getElementById("answer_text").innerText = data.answer;
        document.getElementById("answer_text").classList.remove("hidden");
        document.getElementById("aiModalContent").innerText = data.answer;
    }
}

function fillSQL(data) {
    if (!data.sql) return;
    document.getElementById("sql_button").classList.remove("hidden");
    document.getElementById("sql_pre").innerText = data.sql;
}

/* -----------------------------------------
   ⚡ KEEP THE EXACT TABLE FORMAT YOU HAD
------------------------------------------ */
function buildTable(columns, rows) {
    if (!columns || !rows || rows.length === 0) return;

    document.getElementById("table_wrapper").classList.remove("hidden");

    const head = document.getElementById("table_head");
    const body = document.getElementById("table_body");

    head.innerHTML = `
        <tr>
            ${columns.map(col => `<th><div class="flex items-center justify-between gap-2"><p>${titleFormat(col)}</p></div></th>`).join("")}
        </tr>
    `;

    body.innerHTML = rows.map(row => {
        return `
            <tr class="hover:bg-gray-100 dark:hover:bg-gray-800">
                ${columns.map(col => `<td style="white-space: normal">${formatValue(col, row[col])}</td>`).join("")}
            </tr>
        `;
    }).join("");
}

/* -----------------------------------------
   ⚡ FULL FORMATTER (matches original Jinja)
------------------------------------------ */
function formatValue(col, val) {
    if (val === null || val === "") return "-";

    const lower = col.toLowerCase();

    // Badge logic
    if (lower.includes("estatus")) {
        const badgeClass = 
              purple_badge_values.includes(val) ? "bg-purple text-white"
            : success_badge_values.includes(val) ? "bg-success text-white"
            : danger_badge_values.includes(val)  ? "bg-danger text-white"
            : warning_badge_values.includes(val) ? "bg-warning"
            : primary_badge_values.includes(val) ? "bg-primary text-white"
            : gray_badge_values.includes(val)    ? "bg-gray/10"
            : "bg-a text-white";

        return `<div class="inline-flex items-center rounded-full text-xs justify-center px-2.5 py-1.5 ${badgeClass}">
                    ${val}
                </div>`;
    }

    // Money format
    if (money_format_columns.includes(col)) {
        return Number(val).toLocaleString('en-US', { style: "currency", currency: "USD" });
    }

    // Percentage format
    if (percentage_format_columns.includes(col)) {
        return val + "%";
    }

    // Numbers
    if (typeof val === "number") {
        return val.toLocaleString("en-US");
    }

    return val;
}

function showError(msg) {
    document.getElementById("error_text").innerText = msg;
    document.getElementById("error_wrapper").classList.remove("hidden");
}