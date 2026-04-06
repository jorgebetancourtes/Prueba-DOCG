function rebindSelect2(root = document) {
  	root.querySelectorAll('select.searchable-select').forEach(el => {
		if (!el.isConnected) return;
		if ($(el).data('select2')) return;

		const options = {
		width: '100%',
		dropdownParent: $(el).parent()
		};

		if (allow_new_value_dropdowns.includes(el.name)) {
		options.tags = true;
		options.createTag = params => {
			const term = $.trim(params.term);
			if (!term) return null;
			return { id: term, text: term };
		};
		options.insertTag = (data, tag) => data.unshift(tag);
		}

		$(el)
		.off('change.select2sync')
		.select2(options)
		.on('change.select2sync', function () {
			const alpineRoot = el.closest('[x-data]');
			const alpineData = Alpine.$data(alpineRoot);
			if (!alpineData?.items) return;

			const col = el.name;
			const recordId = el.id.split('_').pop();
			const record = alpineData.items.find(r => String(r.id) === recordId);
			if (!record) return;

			record[col] = el.value;
			update_record(record, col);
      	});
  });
}
$(document).on('select2:open', () => {
    document.querySelector('.select2-container--open .select2-search__field')?.focus();
});