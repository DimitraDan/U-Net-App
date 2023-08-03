let canvasPoints = {};

function getCoordinates(index) {
  document.getElementById("x" + index).value = canvasPoints["canvas" + index].x;
  document.getElementById("y" + index).value = canvasPoints["canvas" + index].y;
}

function drawImage(id, imageUrl) {
  // Reset arrays before drawing on a new canvas
  canvasPoints[id] = { x: [], y: [] };

  const canvas = document.getElementById(id);
  const context = canvas.getContext("2d");

  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;

  // Load the image onto the canvas
  const image = new Image();
  image.src = imageUrl;

  image.onload = () => {
    // Calculate the aspect ratio of the image
    const aspectRatio = image.width / image.height;

    // Set the canvas size to fit the image while maintaining its aspect ratio
    let canvasWidth = 300;
    let canvasHeight = canvasWidth / aspectRatio;

    // If the height exceeds 300 pixels, adjust the width instead
    if (canvasHeight > 300) {
      canvasHeight = 300;
      canvasWidth = canvasHeight * aspectRatio;
    }

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    // Draw the image with the correct aspect ratio
    context.drawImage(image, 0, 0, canvasWidth, canvasHeight);
  };

  function draw(e) {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Scale the coordinates to the original image size
    const originalX = x * (image.width / canvas.width);
    const originalY = y * (image.height / canvas.height);

    // Store the original coordinates in the canvasPoints object
    canvasPoints[id].x.push(originalX);
    canvasPoints[id].y.push(originalY);

    context.strokeStyle = "#000000";
    context.lineJoin = "round";
    context.lineCap = "round";
    context.lineWidth = 5;

    context.beginPath();
    context.moveTo(lastX, lastY);
    context.lineTo(x, y);
    context.stroke();

    [lastX, lastY] = [x, y];
  }

  canvas.addEventListener("mousedown", (e) => {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    lastX = e.clientX - rect.left;
    lastY = e.clientY - rect.top;
  });

  canvas.addEventListener("mousemove", draw);
  canvas.addEventListener("mouseup", () => {
    isDrawing = false;
    // Clear the points only if the user actually drew something
    if (canvasPoints[id].x.length === 0) {
      canvasPoints[id].x = [];
      canvasPoints[id].y = [];
    }
  });
  canvas.addEventListener("mouseout", () => {
    isDrawing = false;
    // Clear the points only if the user actually drew something
    if (canvasPoints[id].x.length === 0) {
      canvasPoints[id].x = [];
      canvasPoints[id].y = [];
    }
  });
}

function restartCanvas(imageUrl, index) {
  // Clear the stored lines and points for the selected canvas
  canvasPoints[index].x = [];
  canvasPoints[index].y = [];

  // Get the canvas element
  const canvas = document.getElementById(index);
  const context = canvas.getContext("2d");

  // Clear the canvas by drawing a transparent rectangle over it
  context.clearRect(0, 0, canvas.width, canvas.height);

  // Reload the image on the canvas (replace 'image-url' with the actual URL)
  const image = new Image();
  image.src = imageUrl;
  image.onload = () => {
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
  };
}
