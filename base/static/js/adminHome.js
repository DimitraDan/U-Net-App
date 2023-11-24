let prevScrollPos = window.pageYOffset;

window.onscroll = function() {
    let currentScrollPos = window.pageYOffset;

    if (prevScrollPos > currentScrollPos) {
        document.getElementById("profileHeader").style.top = "0";
    } else {
        document.getElementById("profileHeader").style.top = "-50px"; // Adjust this value as needed
    }

    prevScrollPos = currentScrollPos;
};
