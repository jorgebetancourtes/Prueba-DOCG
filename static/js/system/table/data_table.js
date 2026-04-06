// static/js/data_table.js

window.createDataTable = function (config) {
    return {
        // Datos iniciales
        items: [], // Lista de registros obtenidos del API
        view: parseInt(config.view) || 50, // Número de registros por página
        searchInput: "", // Texto de búsqueda
        filteredStatus: "todos", // Filtro por estado (si se usa)
        pages: [], // Números de páginas para la paginación
        offset: parseInt(config.offset) || 5, // Número de botones a mostrar en paginación
        apiEndpoint: config.apiEndpoint || "/data/read", // Endpoint del API
        searchKeys: config.searchKeys || [],
        sorted: {
            field: config.defaultSortField || "fecha_creado",
            rule: config.defaultSortRule || "desc",
        },
        pagination: {
            total: 0, // Total de registros
            lastPage: 1, // Número de la última página
            perPage: parseInt(config.view) || 50, // Registros por página
            currentPage: 1, // Página actual
            from: 1, // Registro inicial de la página actual
            to: parseInt(config.view) || 50, // Registro final de la página actual
        },
        dateRange:"",
        filters: [],
        // Agregar las columnas pasadas en la configuración
        columns: config.columns || [],

        initData() {
            this.fetchData();
            window.addEventListener("filter-status", (event) => {
                this.filterStatus(event.detail);
            });
            window.addEventListener("refresh-data-table", () => {
                this.fetchData();
            });
            this.$watch('filters', value => {
                this.fetchData();
            });
            document.addEventListener("update-filter", (e) => {
                const { key, value } = e.detail;
                this.filters[key] = value;     // store values by filter name
                this.fetchData();
            });
        },
        

        async fetchData() {
        // 1) Start with the current page params (?foo=bar...)
            const current = new URLSearchParams(window.location.search);

            // 2) Now overlay the component’s state (these take priority)
            current.set("view", String(this.view));
            current.set("search", this.searchInput ?? "");
            current.set("status", this.filteredStatus ?? "todos");
            current.set("sortField", this.sorted.field ?? "fecha_creado");
            current.set("sortRule", this.sorted.rule ?? "desc");
            current.set("page", String(this.pagination.currentPage));
            current.set("dateRange", this.dateRange ?? "");
            for (const [key, arr] of Object.entries(this.filters)) {
                current.set(key, arr.join(","));  // ?id_proveedor=1,2,3
            }
            try {
                showLoader();
                const url = `${this.apiEndpoint}?${current.toString()}`;
                const response = await fetch(url);
                const data = await response.json();

                this.items = data.items || [];
                this.pagination.total = data.total || 0;
                this.pagination.lastPage = data.pages || 1;
                this.viewPage(this.pagination.currentPage);
            } catch (error) {
                console.error("Error al obtener los datos:", error);
            } finally {
                hideLoader();
            }
        },


        filterStatus(status) {
            this.filteredStatus = status;
            this.fetchData();
        },

        search(value) {
            this.searchInput = value;
            this.fetchData();
        },

        sort(field, rule) {
            this.sorted.field = field;
            this.sorted.rule = rule;
            this.fetchData();
        },
        changePage(page){
            this.pagination.currentPage=page;
            this.fetchData();
        },

        viewPage(page) {
            if (page >= 1 && page <= this.pagination.lastPage) {
                this.pagination.currentPage = page;
                const total = this.pagination.total;
                const from = (page - 1) * this.view + 1;
                let to = page * this.view;
                if (page === this.pagination.lastPage) {
                    to = total;
                }
                this.pagination.from = from;
                this.pagination.to = to;
                this.showPages();
            }
        },

        showPages() {
            const pages = [];
            let startPage = this.pagination.currentPage - Math.floor(this.offset / 2);
            if (startPage < 1) startPage = 1;
            let endPage = startPage + this.offset - 1;
            if (endPage > this.pagination.lastPage) endPage = this.pagination.lastPage;
            for (let i = startPage; i <= endPage; i++) {
                pages.push(i);
            }
            this.pages = pages;
        },

        changeView() {
            this.view = parseInt(this.view);
            this.pagination.perPage = this.view;
            this.fetchData();
        },

        initDatePicker() {
            flatpickr("#dateRange", {
                mode: "range",
                dateFormat: "Y-m-d",
                allowInput: true,

                onChange: (selectedDates, dateStr, instance) => {
                    if (selectedDates.length === 1) {
                        // User picked one date → temporarily wait for second date
                        return;
                    }

                    if (selectedDates.length === 2) {
                        const [start, end] = selectedDates;

                        // If both dates are the same → build same-day range string
                        if (start.getTime() === end.getTime()) {
                            const singleDate = instance.formatDate(start, "Y-m-d");
                            dateStr = `${singleDate} to ${singleDate}`;
                        }

                        this.dateRange = dateStr;
                        this.fetchData();
                    }
                }
            });
        },



        isEmpty() {
            return this.pagination.total === 0;
        },
    };
};
