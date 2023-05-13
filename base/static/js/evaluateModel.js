const x_points = [];
const y_points = [];

function drawOnImage(image, counter) {
    document.getElementById('x_points'+counter).value ='';
    document.getElementById('y_points'+counter).value = '';
    const canvas = document.getElementById('canvas'+counter);
    const context = canvas.getContext("2d");
    context.lineWidth = 5;
    context.lineCap = "round";
    context.strokeStyle = "red";

    canvas.addEventListener('mousedown', e => {
        context.beginPath();
        x_points.push(e.offsetX);
        y_points.push(e.offsetY);
        context.moveTo(e.offsetX, e.offsetY);
        canvas.addEventListener('mousemove', onMouseMove);
    });

    canvas.addEventListener('mouseup', () => {
        canvas.removeEventListener('mousemove', onMouseMove);
    });

    function onMouseMove(e) {
        x_points.push(e.offsetX);
        y_points.push(e.offsetY);
        document.getElementById('x_points'+counter).value = e.offsetX +','+document.getElementById('x_points'+counter).value;
        document.getElementById('y_points'+counter).value = e.offsetY +','+document.getElementById('y_points'+counter).value;
        context.lineTo(e.offsetX, e.offsetY);
        context.stroke();
    }

    if (image) {
        const imageWidth = image.width;
        const imageHeight = image.height;
        
        // rescaling the canvas element
        canvas.width  = imageWidth;
        canvas.height = imageHeight;
        context.drawImage(image, 0, 0, imageWidth, imageHeight);

    }
        

    return {x_points, y_points};
}

function enableDrawing(canvasId, image, counter) {
    document.getElementById(canvasId).addEventListener("mousedown", () => {
        drawOnImage(image, counter);
    });
}

function disableDrawing(canvasId) {
    document.getElementById(canvasId).removeEventListener("mousedown", onMouseDown);
}

function onMouseDown(e) {
    drawOnImage(e.target, counter);
}

function drawImage(url, counter) {
    const image = new Image();
    image.src = url;
    image.onload = () => {
        const canvas = document.getElementById("canvas" + counter);
        const paintButton = document.getElementById("paint-button" + counter);

        // add a click event listener to the "Paint" button
        paintButton.addEventListener("click", () => {
            enableDrawing(canvas);
        });

        // add a click event listener to the canvas to disable drawing
        canvas.addEventListener("mouseleave", () => {
            disableDrawing(canvas);
        });
        // Return the x and y points for each canvas
        const {x_points, y_points} = drawOnImage(image, counter);
    };
  
    return false;
}

function fullscreen(id){
    var el = document.getElementById(id);
  
    if(el.webkitRequestFullScreen) {
        el.webkitRequestFullScreen();
    }
   else {
      el.mozRequestFullScreen();
   }            
  }


  function toggleSwitch(input) {
    var roundBox = input.nextElementSibling.nextElementSibling;
    var switchLeft = roundBox.nextElementSibling;
    var switchRight = switchLeft.nextElementSibling;
  
    if (input.checked) {
      roundBox.style.transform = "translate(25px, -50%)";
      switchLeft.querySelector("span").style.opacity = 1;
      switchRight.querySelector("span").style.opacity = 0;
    } else {
      roundBox.style.transform = "";
      switchLeft.querySelector("span").style.opacity = 0;
      switchRight.querySelector("span").style.opacity = 1;
    }
  }
  

  


  $(document).ready(function () {
    $(document).on("click", ".MultiCheckBox", function () {
        var detail = $(this).next();
        detail.show();
    });

    var multipleCancelButton = new Choices('#choices-multiple-remove-button', {
        removeItemButton: true,
        });
       

    $(document).on("click", ".MultiCheckBoxDetailHeader input", function (e) {
        e.stopPropagation();
        var hc = $(this).prop("checked");
        $(this).closest(".MultiCheckBoxDetail").find(".MultiCheckBoxDetailBody input").prop("checked", hc);
        $(this).closest(".MultiCheckBoxDetail").next().UpdateSelect();
    });

    $(document).on("click", ".MultiCheckBoxDetailHeader", function (e) {
        var inp = $(this).find("input");
        var chk = inp.prop("checked");
        inp.prop("checked", !chk);
        $(this).closest(".MultiCheckBoxDetail").find(".MultiCheckBoxDetailBody input").prop("checked", !chk);
        $(this).closest(".MultiCheckBoxDetail").next().UpdateSelect();
    });

    $(document).on("click", ".MultiCheckBoxDetail .cont input", function (e) {
        e.stopPropagation();
        $(this).closest(".MultiCheckBoxDetail").next().UpdateSelect();

        var val = ($(".MultiCheckBoxDetailBody input:checked").length == $(".MultiCheckBoxDetailBody input").length)
        $(".MultiCheckBoxDetailHeader input").prop("checked", val);
    });

    $(document).on("click", ".MultiCheckBoxDetail .cont", function (e) {
        var inp = $(this).find("input");
        var chk = inp.prop("checked");
        inp.prop("checked", !chk);

        var multiCheckBoxDetail = $(this).closest(".MultiCheckBoxDetail");
        var multiCheckBoxDetailBody = $(this).closest(".MultiCheckBoxDetailBody");
        multiCheckBoxDetail.next().UpdateSelect();

        var val = ($(".MultiCheckBoxDetailBody input:checked").length == $(".MultiCheckBoxDetailBody input").length)
        $(".MultiCheckBoxDetailHeader input").prop("checked", val);
    });

    $(document).mouseup(function (e) {
        var container = $(".MultiCheckBoxDetail");
        if (!container.is(e.target) && container.has(e.target).length === 0) {
            container.hide();
        }
    });
});

var defaultMultiCheckBoxOption = { width: '220px', defaultText: 'Select Below', height: '200px' };

jQuery.fn.extend({
    CreateMultiCheckBox: function (options) {

        var localOption = {};
        localOption.width = (options != null && options.width != null && options.width != undefined) ? options.width : defaultMultiCheckBoxOption.width;
        localOption.defaultText = (options != null && options.defaultText != null && options.defaultText != undefined) ? options.defaultText : defaultMultiCheckBoxOption.defaultText;
        localOption.height = (options != null && options.height != null && options.height != undefined) ? options.height : defaultMultiCheckBoxOption.height;

        this.hide();
        this.attr("multiple", "multiple");
        var divSel = $("<div class='MultiCheckBox'>" + localOption.defaultText + "<span class='k-icon k-i-arrow-60-down'><svg aria-hidden='true' focusable='false' data-prefix='fas' data-icon='sort-down' role='img' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 512' class='svg-inline--fa fa-sort-down fa-w-10 fa-2x'><path fill='currentColor' d='M41 288h238c21.4 0 32.1 25.9 17 41L177 448c-9.4 9.4-24.6 9.4-33.9 0L24 329c-15.1-15.1-4.4-41 17-41z' class=''></path></svg></span></div>").insertBefore(this);
        divSel.css({ "width": localOption.width });

        var detail = $("<div class='MultiCheckBoxDetail'><div class='MultiCheckBoxDetailHeader'><input type='checkbox' class='mulinput' value='-1982' /><div>Select All</div></div><div class='MultiCheckBoxDetailBody'></div></div>").insertAfter(divSel);
        detail.css({ "width": parseInt(options.width) + 10, "max-height": localOption.height });
        var multiCheckBoxDetailBody = detail.find(".MultiCheckBoxDetailBody");

        this.find("option").each(function () {
            var val = $(this).attr("value");

            if (val == undefined)
                val = '';

            multiCheckBoxDetailBody.append("<div class='cont'><div><input type='checkbox' class='mulinput' value='" + val + "' /></div><div>" + $(this).text() + "</div></div>");
        });

        multiCheckBoxDetailBody.css("max-height", (parseInt($(".MultiCheckBoxDetail").css("max-height")) - 28) + "px");
    },
    UpdateSelect: function () {
        var arr = [];

        this.prev().find(".mulinput:checked").each(function () {
            arr.push($(this).val());
        });

        this.val(arr);
    },
});


   
   
   
   
   
   
