function imgSelected() {
   document.getElementById('fheight').disabled = false; 
   document.getElementById('fwidth').disabled = false; 
   document.getElementById('submit').disabled = false; 
}

window.addEventListener("beforeunload",function(e){
   document.body.className = "page-loading";
},false);

function showImage(img) {
   document.getElementById("img").src = img
}


function Loaded() {
   document.getElementById("PreLoaderBar").style.display = "none";
}
