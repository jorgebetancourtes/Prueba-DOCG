function openSqlModal() {
    document.getElementById('sqlModalBackdrop')?.classList.remove('hidden');
    document.getElementById('sqlModal')?.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}
function closeSqlModal() {
    document.getElementById('sqlModalBackdrop')?.classList.add('hidden');
    document.getElementById('sqlModal')?.classList.add('hidden');
    document.body.style.overflow = '';
}
function copySqlToClipboard() {
    const modalText = document.getElementById("sql_pre").innerText;
    navigator.clipboard.writeText(modalText).then(() => {
        showSuccess("Querie copiado al portapapeles.");
    }); 
}

function openAiModal() {

    const modal = document.getElementById("aiModal")
    const backdrop = document.getElementById("aiModalBackdrop");
    modal.classList.remove("hidden");
    backdrop.classList.remove("hidden");
}

function closeAiModal() {
    document.getElementById("aiModal").classList.add("hidden");
    document.getElementById("aiModalBackdrop").classList.add("hidden");
}

function copyAiSummary() {
    const modalText = document.getElementById("aiModalContent").innerText;
    navigator.clipboard.writeText(modalText).then(() => {
        showSuccess("Texto copiado al portapapeles.");
    });
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape'){
        closeSqlModal();
        closeAiModal();
    }
});