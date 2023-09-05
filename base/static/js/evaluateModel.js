document.write('<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"><\/script>');
document.write('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"><\/script>');
document.write('<script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"><\/script>');


let canvasPoints = {};

function getCoordinates(index) {
    document.getElementById("x" + index).value = canvasPoints["canvas" + index].x;
    document.getElementById("y" + index).value = canvasPoints["canvas" + index].y;
}

function drawImage(id, imageUrl) {
    // Reset arrays before drawing on a new canvas
    canvasPoints[id] = {x: [], y: []};

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

$(document).ready(function () {
    $('#checkImagesBtn').click(function () {
        const numberOfImages = parseInt($('#numberOfImages').val());
        const section = $('#section').val();
        checkFirstNImages(section, numberOfImages);
    });
});

$(document).ready(function () {
    $('#checkFinalImagesBtn').click(function () {
        const numberOfImages = parseInt($('#numberOfFinalImages').val());
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


$(document).ready(function () {
    $('#imageTable').DataTable({
        "paging": true,
        "searching": true,
        "lengthMenu": [[3, 10, 25, 50, -1], [5, 10, 25, 50, "All"]],
        "info": true,
        columnDefs: [{"orderable": false, "targets": 'no-sort'}]
    });
});

function submitForm(formElement) {
    const formData = new FormData(formElement);
    const loadingSpinnerStep3 = document.getElementById('loadingSpinner');
    loadingSpinnerStep3.style.display = 'block';

    fetch('/predictMask', {
        method: 'POST', body: formData
    })
        .then(response => response.json())
        .then(data => {
            const step3TableBody = $('#step3TableBody');
            step3TableBody.empty(); // Clear existing data

            for (let i = 0; i < data.evaluation.length; i++) {
                step3TableBody.append(`
                            <tr>
                              <td>${i + 1}</td>
                              <td><img src="${data.evaluation[i].image}" alt="Image"></td>
                              <td><img src="${data.evaluation[i].prediction}" alt="Mask"></td>
                              <td>
                                <input type="hidden" id="counter" name="counter" value="${data.evaluation.length}">
                                <input type="hidden" id="x${i + 1}" name="x${i + 1}">
                                <input type="hidden" id="y${i + 1}" name="y${i + 1}">
                                <input name="image${i + 1}" type="hidden" value="${data.evaluation[i].image}">
                                <input name="mask${i + 1}" type="hidden" value="${data.evaluation[i].prediction}">
                                <div class="canvas-container">
                                  <canvas onmouseleave="getCoordinates(${i + 1})" id="canvas${i + 1}" class="drawing-canvas"></canvas>
                                  <button type="button" onclick="restartCanvas('${data.evaluation[i].image}', 'canvas${i + 1}')">Restart
                                  <i class="fas fa-redo"></i>
                                  </button>
                                </div>
                              </td>
                            </tr>
                `);
                drawImage(`canvas${i + 1}`, `${data.evaluation[i].image}`)
            }
            loadingSpinnerStep3.style.display = 'none';
            nextTab()
        })
        .catch(error => {
            console.error('Error:', error);
            loadingSpinnerStep3.style.display = 'none';

        })
}

function submitCorrectedImages(formElement) {
    const formData = new FormData(formElement);
    const loadingSpinnerStep4 = document.getElementById('loadingSpinnerStep4');
    loadingSpinnerStep4.style.display = 'block';

    fetch('/correctMasks', {
        method: 'POST', body: formData
    })
        .then(response => response.json())
        .then(data => {
            const step4TableBody = $('#step4TableBody');
            step4TableBody.empty();
            for (let i = 0; i < data.train_images.length; i++) {
                step4TableBody.append(`
                <tr>
                    <td>
                       <input type="checkbox" name="selectedImages" value="${i + 1}">
                    </td>
                    <td><img src="${data.train_images[i].image}" alt="Image"></td>
                    <td><img src="${data.train_images[i].mask}" alt="Mask"></td>
                    <td>${data.train_images[i].corrected}</td>
                    <input name="image${i + 1}" type="hidden" value="${data.train_images[i].image}">
                    <input name="mask${i + 1}" type="hidden" value="${data.train_images[i].mask}">
                </tr>
            `);
            }
            loadingSpinnerStep4.style.display = 'none';
            nextTab();
        });
}
