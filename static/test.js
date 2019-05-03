let canvas = document.getElementById("canvas");
// let selectColor = false;
let context = {
    selectColor: false,
    fillColorRBG: null,
    fillColorHex: null,
    defaultColorRBG: null,
    defaultColorHex: null,
    x: null,
    y: null
}

function getPosition(obj) {
    let curleft = 0, curtop = 0;
    if (obj.offsetParent) {
        do {        
            curleft += obj.offsetLeft;
            curtop += obj.offsetTop;
        } while (obj = obj.offsetParent);
        return { x: curleft, y: curtop };
    }
    return undefined;
}

function rgbToHex(r, g, b) {
    if (r > 255 || g > 255 || b > 255)
        throw "Invalid color component";
    return ((r << 16) | (g << 8) | b).toString(16);
}

function hexToRgb(hex) {
    let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function drawImageFromWebUrl(sourceurl){
      let img = new Image();
      img.addEventListener("load", function () {
          // The image can be drawn from any source
          canvas.getContext("2d").drawImage(img, 0, 0, img.width, img.height, 0, 0, canvas.width, canvas.height);
      });
      img.setAttribute("src", sourceurl);
}

function fillColor(obj, x, y, r, g, b, ctx) {
    obj.data[0] = r;
    obj.data[1] = g;
    obj.data[2] = b;
    ctx.putImageData(obj, x, y);
}

function floodFill(x, y, ctx) {
    let p = ctx.getImageData(x, y, 1, 1);
    let hex = "#" + ("000000" + rgbToHex(p.data[0], p.data[1], p.data[2])).slice(-6);
    if (context.selectColor && hex === context.defaultColorHex) {
        fillColor(p, x, y, context.fillColorRGB.r, context.fillColorRGB.g, context.fillColorRGB.b, ctx);
        floodFill(x-1, y, ctx);
        floodFill(x+1, y, ctx);
        floodFill(x, y+1, ctx);
        floodFill(x, y-1, ctx);
        floodFill(x+1, y+1, ctx);
        floodFill(x+1, y-1, ctx);
        floodFill(x-1, y+1, ctx);
        floodFill(x-1, y-1, ctx);
    }
}

// Draw a base64 image because this is a fiddle, and if we try with an image from URL we'll get tainted canvas error
// Read more about here : http://ourcodeworld.com/articles/read/182/the-canvas-has-been-tainted-by-cross-origin-data-and-tainted-canvases-may-not-be-exported
drawImageFromWebUrl(imageLinkB64);

canvas.addEventListener("click",function(e){
    let pos = getPosition(this);
    let x = e.x - pos.x;
    let y = e.y - pos.y;
    let ctx = canvas.getContext('2d');
    let p = ctx.getImageData(x, y, 1, 1);
    let hex = "#" + ("000000" + rgbToHex(p.data[0], p.data[1], p.data[2])).slice(-6);
    context.defaultColorHex = hex;
    context.defaultColorRBG = hexToRgb(hex);
    floodFill(x, y, ctx);
},false);

let colorPicker = document.getElementById('colorPicker');

colorPicker.addEventListener('change', () => {
    context.selectColor = true;
    context.fillColorRGB = hexToRgb(colorPicker.value);
    context.fillColorHex = colorPicker.value;
})
