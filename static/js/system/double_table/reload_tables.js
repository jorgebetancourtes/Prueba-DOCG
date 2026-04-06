async function reload_tables(){
    const tableEl = document.querySelector('[x-data="tabla"]');
    if (tableEl) {
        const comp = Alpine.$data(tableEl);
        if (comp?.reload) {
            await comp.reload();
        }
    }
    const tableEl2 = document.querySelector('[x-data="tabla2"]');
    if (tableEl2) {
        const comp = Alpine.$data(tableEl2);
        if (comp?.reload) {
            await comp.reload();
        }
    }
    Alpine.nextTick(() => rebindSelect2());
}