 
    flatpickr("#dateRange", {
        mode: "range",
        dateFormat: "Y-m-d"
    });

function modernMultiSelect() {
    return {
        open: false,
        search: "",
        options: [
            { value: 'af2c75e5-e4f7-4ea6-8d25-7f8ce9aab30c', text: 'Mining' },
            { value: 'f6cc5c14-e010-4c15-91e6-26868e34c5ac', text: 'Foods' },
            { value: '22415280-c711-4e56-b13d-3f3a733b8a84', text: 'Otro' },
        ],
        selected: [],
        get selectedOptions() {
            return this.options.filter(opt => this.selected.includes(opt.value));
        },
        get filteredOptions() {
            if (this.search.trim() === "") return this.options;
            return this.options.filter(opt =>
                opt.text.toLowerCase().includes(this.search.trim().toLowerCase())
            );
        },
        toggleOption(option) {
            if (this.selected.includes(option.value)) {
                this.selected = this.selected.filter(val => val !== option.value);
            } else {
                this.selected.push(option.value);
            }
        },
        removeOption(option) {
            this.selected = this.selected.filter(val => val !== option.value);
        },
        isSelected(option) {
            return this.selected.includes(option.value);
        }
    }
}