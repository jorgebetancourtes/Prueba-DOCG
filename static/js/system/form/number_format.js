document.querySelectorAll(".number-format").forEach(input => {
    if (input.value) {
        input.value = formatNumber(input.value);
    }

    input.addEventListener("input", function () {
        let start = this.selectionStart;
        let oldValue = this.value;

        // Remove commas
        let raw = oldValue.replace(/,/g, '');

        // Allow only numbers and ONE dot
        if (!/^\d*\.?\d*$/.test(raw)) {
            this.value = raw.slice(0, -1); // remove bad char
            return;
        }

        // 🔥 KEY FIX: don't format if user just typed "."
        if (raw.endsWith(".")) {
            this.value = raw; // keep exactly what user typed
            return;
        }
        if (raw.endsWith(".0")) {
            this.value = raw; // keep exactly what user typed
            return;
        }
        let formatted = formatNumber(raw);
        this.value = formatted;

        // Fix cursor position
        let diff = formatted.length - oldValue.length;
        let newCursor = start + diff;
        this.setSelectionRange(newCursor, newCursor);
    });

    input.form?.addEventListener("submit", () => {
        input.value = input.value.replace(/,/g, '');
    });
});

function formatNumber(value) {
    if (value === "") return "";

    // Allow just "."
    if (value === ".") return ".";

    let hasTrailingDot = value.endsWith(".");

    let parts = value.split(".");
    let integerPart = parts[0];
    let decimalPart = parts[1];

    let formattedInt = integerPart
        ? Number(integerPart).toLocaleString("en-US")
        : "";

    let result = formattedInt;

    // ✅ FIX: check using parts.length instead
    if (parts.length > 1) {
        result += "." + (decimalPart ?? "");
    }

    // (optional safety, but not strictly needed anymore)
    if (hasTrailingDot && !result.endsWith(".")) {
        result += ".";
    }

    return result;
}