window.addEventListener("beforeunload", function (e) {
    document.body.className = "page-loading";
}, false);