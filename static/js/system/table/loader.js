// static/js/loader.js

function showLoader() {
    const loader = document.getElementById("loading-popup");
    if (loader) {
        loader.classList.remove("hidden");
    }
}

function hideLoader() {
    const loader = document.getElementById("loading-popup");
    if (loader) {
        loader.classList.add("hidden");
    }
}
