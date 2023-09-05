document.write('<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>')
document.write('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"></script>')
document.write('<script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>')

$(document).ready(function () {
    $('#run-table').DataTable({
        "paging": true,
        "searching": true,
        "lengthMenu": [[3, 10, 25, 50, -1], [5, 10, 25, 50, "All"]],
        "info": true,
        columnDefs: [
            {"orderable": false, "targets": 'no-sort'}
        ]
    });
});

$(document).ready(function () {
    $('#imageTable').DataTable({
        "paging": true,
        "searching": true,

        "lengthMenu": [[3, 10, 25, 50, -1], [5, 10, 25, 50, "All"]],
        "info": true,
        "columnDefs": [
            {"orderable": false, "targets": "no-sort"}
        ]
    });
});

function submitForm(event) {
    event.preventDefault();

    // Collect form data
    const formData = new FormData(event.target);

    // Get the original DataTable
    const originalTable = $('#imageTable').DataTable();

    // Iterate over each page of the original table
    for (let page = 0; page < originalTable.page.info().pages; page++) {
        // Go to the specific page
        originalTable.page(page).draw(false);

        // Get all the checkboxes on the current page
        const checkboxes = originalTable.column(0).nodes().to$().find('input[name="selectedImages"]');
        checkboxes.each(function () {
            if (this.checked) {
                formData.append('selectedImages', this.value);
            }
        });
    }

    // Create a new form dynamically
    const newForm = document.createElement('form');
    newForm.method = 'POST';
    newForm.action = '/train_selected';
    newForm.style.display = 'none'; // Hide the form from the user

    // Append all form data as hidden fields to the new form
    for (const pair of formData.entries()) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = pair[0];
        input.value = pair[1];
        newForm.appendChild(input);
    }

    // Append the new form to the document body
    document.body.appendChild(newForm);

    // Submit the new form
    newForm.submit();
}

$(document).ready(function () {
    $('#checkAllBtn').click(function () {
        const numberOfImages = parseInt($('#numberOfImages').val());
        checkFirstNImages('selectedImages', numberOfImages);
    });
});

function checkFirstNImages(section, numberOfImages) {
    const originalTable = $('#imageTable').DataTable();
    const checkboxes = originalTable.column(0).nodes().to$().find(`input[name="${section}"]`);

    checkboxes.prop('checked', false); // Uncheck all checkboxes

    const firstNCheckboxes = checkboxes.slice(0, numberOfImages);
    firstNCheckboxes.prop('checked', true); // Check the first N checkboxes

    firstNCheckboxes.each(function () {
        toggleCheckmark(this);
        $(this).on('dblclick', function () {
            $(this).prop('checked', false);
            toggleCheckmark(this);
        });
    });
}

function toggleCheckmark(checkbox) {
    if (checkbox && checkbox.parentNode) {
        const checkmark = checkbox.parentNode.querySelector('.checkmark');
        if (checkmark) {
            checkmark.style.display = checkbox.checked ? 'inline-block' : 'none';
        }
    }
}

// Open the form
function openForm() {
    document.getElementById("myForm").style.display = "block";
}

// Close the form
function closeForm() {
    document.getElementById("myForm").style.display = "none";
}

// Handle next and previous buttons
var currentTab = 0;
var form = document.getElementById("msform");
var fieldsets = form.getElementsByTagName("fieldset");

function nextTab() {
    fieldsets[currentTab].style.display = "none";
    currentTab = currentTab + 1;
    if (currentTab >= fieldsets.length) {
        form.submit();
        return false;
    }
    showTab(currentTab);
}

function previousTab() {
    fieldsets[currentTab].style.display = "none";
    currentTab = currentTab - 1;
    showTab(currentTab);
}

function showTab(tabIndex) {
    fieldsets[tabIndex].style.display = "block";
    updateProgress(tabIndex);
}

function updateProgress(tabIndex) {
    var progressBar = document.getElementById("progressbar");
    var progressItems = progressBar.getElementsByTagName("li");
    for (var i = 0; i < progressItems.length; i++) {
        progressItems[i].className = (i <= tabIndex) ? "active" : "";
    }
}
