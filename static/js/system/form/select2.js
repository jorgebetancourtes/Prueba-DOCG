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
     });
} 
document.addEventListener('DOMContentLoaded', () => {
     rebindSelect2();
});        
$(document).ready(function () {
    $("form").on("submit", function () {
        $(this)
            .find(":input:disabled")
            .prop("disabled", false);
    });
});
$(document).ready(function () {
    $('.js-example-basic-multiple').select2({
        width: '100%',
        dropdownAutoWidth: true,
    });
});  
$(document).on('select2:open', () => {
    document.querySelector('.select2-container--open .select2-search__field')?.focus();
});