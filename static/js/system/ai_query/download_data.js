function download_ai_data() {
    if (typeof columns === "undefined" || typeof rows === "undefined") {
        alert("No hay datos para descargar");
        return;
    }

    if (!rows || rows.length === 0) {
        alert("No hay datos para descargar");
        return;
    }

    // Build CSV with UTF-8 BOM for Excel compatibility
    let csv = "\uFEFF"; // BOM

    // Header
    csv += columns.join(",") + "\n";

    // Rows
    rows.forEach(row => {
        let line = columns.map(col => {
            let value = row[col];

            if (value === null || value === undefined) value = "";

            // Convert to string
            value = String(value);

            // Escape quotes
            value = value.replace(/"/g, '""');

            return `"${value}"`;
        }).join(",");

        csv += line + "\n";
    });

    // Create CSV as Blob
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    // Create temp link
    const link = document.createElement("a");
    link.href = url;

    // Filename with timestamp
    const timestamp = new Date().toISOString().slice(0,19).replace(/[:T]/g, "-");
    link.download = `consulta_ai_${timestamp}.csv`;

    // Trigger download
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}