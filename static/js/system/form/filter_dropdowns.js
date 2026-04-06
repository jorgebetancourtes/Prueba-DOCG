// filter
Object.entries(filters).forEach(([childColumn, parentColumn]) => {
	const $parent = $(`#${parentColumn}`);
	const $child = $(`#${childColumn}`);
	if ($parent.length === 0 || $child.length === 0) return;
	// Save all original options (excluding the default one)
	const allOptions = $child.find("option").not('[value=""]').clone();
	function filterChildOptions() {
		const selectedValue = $parent.val();
		// Clear everything
		$child.empty();
		// Always add default option
		$child.append('<option value="">Selecciona una opción</option>');
		// Append only matching options
		allOptions
		.filter((_, opt) => $(opt).data("filter") == selectedValue)
		.each((_, opt) => $child.append($(opt).clone()));
	}
	// Attach listener
	$parent.on("change", filterChildOptions);
	// Run once at page load
	filterChildOptions();
});

// filter from multi select
function filterSelectOptionsByIds(selectElement, allowedIds) {
    const allowedSet = new Set(allowedIds.map(String));
	const $select = $(selectElement);
	const allOptions = $select.find("option").not('[value=""]').clone();
	$select.empty();
	$select.append('<option value="">Selecciona una opción</option>');
    allOptions.each(function () {
        const value = String($(this).val() || "");

        if (!value) return;

        if (allowedSet.has(value)) {
            $select.append($(this).clone());
        }
    });
    $select.val(null);

    // Refresh Select2
    if ($select.hasClass("select2-hidden-accessible")) {
        $select.trigger("change.select2");
    } else {
        $select.trigger("change");
    }
}