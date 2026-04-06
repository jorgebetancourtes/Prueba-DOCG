async function reload_table(){
    const tableEl = document.querySelector('[x-data="tabla"]');
    if (tableEl) {
        const comp = Alpine.$data(tableEl);
        if (comp?.reload) {
            await comp.reload();
        }
    }
}    
