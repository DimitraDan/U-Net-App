
var all_points_x = []; 
var all_points_y = []; 


// enabling drawing on the blank canvas
drawOnImage();

var quotes = [
  "If the mask is wrong report it and help us improve our model by drawing the outline where the skin lesion is.", 
  "For fullscreen double click the image below."]
  document.getElementById('info').innerHTML = quotes[0];

function drawImage(url) {
  document.getElementById('report').value= "Try again";
  document.getElementById('report').addEventListener('click', event => {
    tryAgain();
  });
  document.getElementById('report').style.backgroundColor= "#2b82df";


  document.getElementById('info').innerHTML = quotes[1];
  document.getElementById('submitReport').style.display = "block";
  document.getElementById('tools').style.display = "block";

  const image = new Image();
  image.src = url;

  image.onload = () => {
    drawOnImage(image)
  }

  return false;
}

function getCoordinates() {
  document.getElementById('i').value = document.getElementById('image').src;
  document.getElementById('m').value = document.getElementById('mask').src;
  document.getElementById('im').value = document.getElementById('imageAndMask').src;

  document.getElementById('x').value = all_points_x;
  document.getElementById('y').value = all_points_y;
}

const sizeElement = document.querySelector("#sizeRange");
let size = sizeElement.value;
sizeElement.oninput = (e) => {
  size = e.target.value;
};

const colorElement = document.getElementsByName("colorRadio");
let color;
colorElement.forEach((c) => {
  if (c.checked) color = c.value;
});
colorElement.forEach((c) => {
  c.onclick = () => {
    color = c.value;
  };
});

function getMousePos(canvas, evt) {
  let rect = canvas.getBoundingClientRect();
  return {
    x: Math.round( (evt.clientX - rect.left) / (rect.right - rect.left) * canvas.width ),
    y: Math.round((evt.clientY - rect.top) / (rect.bottom - rect.top) * canvas.height )
};
}

function drawOnImage(image = null) {
  const canvasElement = document.getElementById("canvas");
  const context = canvasElement.getContext("2d");

  
  // if an image is present,
  // the image passed as parameter is drawn in the canvas
  if (image) {
    const imageWidth = image.width;
    const imageHeight = image.height;
    
    // rescaling the canvas element
    canvas.width  = imageWidth;
    canvas.height = imageHeight;
     
    
    context.drawImage(image, 0, 0, imageWidth, imageHeight);
  }
  
  
let isDrawing;
  

  canvasElement.onmousedown = (e) => {
    isDrawing = true;
    context.beginPath();
    context.lineWidth = size;

    context.globalCompositeOperation="source-over";
    context.strokeStyle = color;

    context.lineJoin = "round";
    context.lineCap = "round";
    let pos = getMousePos(canvasElement, e)
    context.moveTo(pos.x , pos.y);
  };
  
  canvasElement.onmousemove = (e) => {
    if (isDrawing) { 
      let pos = getMousePos(canvasElement, e)

        all_points_x.push(pos.x);
        all_points_y.push(pos.y);

      context.lineTo(pos.x, pos.y);
      context.stroke();
    }
  };
  
  canvasElement.onmouseup = function () {
    isDrawing = false;
    context.closePath();
  };
}

function tryAgain() {
  all_points_x = []
  all_points_y = []
}

function fullscreen(){
  var el = document.getElementById('canvas');

  if(el.webkitRequestFullScreen) {
      el.webkitRequestFullScreen();
  }
 else {
    el.mozRequestFullScreen();
 }            
}

