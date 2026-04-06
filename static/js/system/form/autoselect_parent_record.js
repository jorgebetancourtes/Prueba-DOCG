    document.addEventListener('DOMContentLoaded', function() {
        const params = new URLSearchParams(window.location.search);
        const id_parent_record = params.get('id_parent_record');

        if (!id_parent_record) return;

        // Helper: safely set value only if the option exists
        const setSelectValueIfExists = ($el, value) => {
            if ($el.find(`option[value="${value}"]`).length > 0) {
                $el.val(value).trigger('change').prop('disabled', true);
                return true;
            }
            return false;
        };

        // Handle list or single select ID
        if (Array.isArray(parent_record)) {
            for (const id of parent_record) {
                const $el = $('#' + id);
                if ($el.length && setSelectValueIfExists($el, id_parent_record)) {
                    break; // stop after successful assignment
                }
            }
        } else {
            const $el = $('#' + parent_record);
            if ($el.length) {
                setSelectValueIfExists($el, id_parent_record);
            }
        }
    });