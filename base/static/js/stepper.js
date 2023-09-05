var currentTab = 0;
var form = document.getElementById("msform");
var fieldsets = form.getElementsByTagName("fieldset");
var progressBar = document.getElementById("progressbar");
var progressItems = progressBar.getElementsByTagName("li");

closeForm()

function showTab(tabIndex) {
    for (var i = 0; i < fieldsets.length; i++) {
        if (i === tabIndex) {
            fieldsets[i].style.display = "block";
            progressItems[i].classList.add("active");
        } else {
            fieldsets[i].style.display = "none";
            progressItems[i].classList.remove("active");
        }
    }
}

function nextTab() {
    if (currentTab < fieldsets.length - 1) {
        currentTab++;
        showTab(currentTab);
    }
}

function previousTab() {
    if (currentTab > 0) {
        currentTab--;
        showTab(currentTab);
    }
}

function openForm() {
    currentTab = 0;
    showTab(currentTab);
    document.getElementById("myForm").style.display = "block";
}

function closeForm() {
    document.getElementById("myForm").style.display = "none";
}
