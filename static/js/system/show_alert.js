function showAlert(message) {
  window.dispatchEvent(new CustomEvent('show-info', { detail: message }));
  infoAlert.style.display = 'flex';
  infoAlert.style.opacity = '1';

  setTimeout(() => {
    infoAlert.style.opacity = '0';
    setTimeout(() => infoAlert.style.display = 'none', 1000);
  }, 3000);
}
function showSuccess(message) {
  window.dispatchEvent(new CustomEvent('show-success', { detail: message }));
  successAlert.style.display = 'flex';
  successAlert.style.opacity = '1';

  setTimeout(() => {
    successAlert.style.opacity = '0';
    setTimeout(() => successAlert.style.display = 'none', 1000);
  }, 3000);
}
function showDanger(message) {
  window.dispatchEvent(new CustomEvent('show-danger', { detail: message }));
  dangerAlert.style.display = 'flex';
  dangerAlert.style.opacity = '1';

  setTimeout(() => {
    dangerAlert.style.opacity = '0';
    setTimeout(() => dangerAlert.style.display = 'none', 1000);
  }, 3000);
}

