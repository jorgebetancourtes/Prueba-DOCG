// static/js/dynamic_table_init.js

document.addEventListener("alpine:init", () => {
    const tableDataElement = document.getElementById("table-data");
    if (!tableDataElement) return;

    const tableName = tableDataElement.getAttribute("data-table");
    const tableColumns = JSON.parse(tableDataElement.getAttribute("data-columns"));

    Alpine.data("tabla", () => {
        const dt = createDataTable({
            apiEndpoint: tableName,
            view: 50,
            offset: 5,
            defaultSortField: "fecha_de_creacion",
            defaultSortRule: "desc",
            searchKeys: tableColumns,
            columns: tableColumns,
        });

        return {
            ...dt,
            async reload() {
                // if createDataTable already has a fetch function, call it here
                if (typeof this.fetchData === "function") {
                    await this.fetchData();
                } else {
                    // fallback: reinitialize data
                    const response = await fetch(this.apiEndpoint);
                    const data = await response.json();
                    this.items = data; // assuming `items` holds the table rows
                }
            },
        };
    });
});

document.addEventListener("alpine:init", () => {
    const tableDataElement = document.getElementById("table-data2");
    if (!tableDataElement) return;

    const tableName = tableDataElement.getAttribute("data-table");
    const tableColumns = JSON.parse(tableDataElement.getAttribute("data-columns"));

    Alpine.data("tabla2", () => {
        const dt = createDataTable({
            apiEndpoint: tableName,
            view: 50,
            offset: 5,
            defaultSortField: "fecha_de_creacion",
            defaultSortRule: "desc",
            searchKeys: tableColumns,
            columns: tableColumns,
        });

        return {
            ...dt,
            async reload() {
                if (typeof this.fetchData === "function") {
                    await this.fetchData();
                } else {
                    const response = await fetch(this.apiEndpoint);
                    const data = await response.json();
                    this.items = data;
                }
            },
        };
    });
});
