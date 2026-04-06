function money_format(value) {
    return `$${new Intl.NumberFormat().format(value)}`;
}
function commafy(value) {
    if (typeof value !== "number" || isNaN(value)) return value; // Keep non-numeric values unchangeda
    return `${new Intl.NumberFormat().format(value)}`;
}
function round(value) {
    if (typeof value !== "number" || isNaN(value)) return value; // Keep non-numeric values unchangeda
    return `${new Intl.NumberFormat().format(value)}`;
}

function date_format(value) {
    if (!value) return value;

    const meses = [
        "enero", "febrero", "marzo", "abril",
        "mayo", "junio", "julio", "agosto",
        "septiembre", "octubre", "noviembre", "diciembre"
    ];

    // 🔥 Parse manual para evitar UTC
    const [year, month, day] = value.split("-").map(Number);
    const date = new Date(year, month - 1, day);

    if (isNaN(date)) return value;

    const dia = date.getDate();
    const mes = meses[date.getMonth()];
    const anio = date.getFullYear();

    return `${dia} ${mes} de ${anio}`;
}

function isDate(value) {
    if (typeof value !== 'string') return false;

    // Matches ISO-like formats: 2024-01-01, 2024-01-01T10:00:00
    const isoPattern = /^\d{4}-\d{2}-\d{2}/;

    if (!isoPattern.test(value)) return false;

    const date = new Date(value);
    return !isNaN(date);
}