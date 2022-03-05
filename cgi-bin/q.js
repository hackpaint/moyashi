var downFlag = false;
var firstDownFlag;
var downX, downY;
var x1, y1;
var x2, y2;
var x3, y3;
var ajax = new XMLHttpRequest();

function canvasToBlob(canvas, callback, type) {
    if (!type) type = 'image/png';
    if (canvas.toBlob) {
	canvas.toBlob(callback, type);
    } else if (canvas.toDataURL && window.Uint8Array && window.Blob && window.atob) {
	var binStr = atob(canvas.toDataURL(type).replace(/^[^,]*,/, ''));
	var len = binStr.length;
	var arr = new Uint8Array(len);
	for (var i = 0; i < len; i++)
	    arr[i] = binStr.charCodeAt(i);
	callback(new Blob([arr], {type: type}));
    } else {
	callback(null);
    }
}

function getter() {
    if (ajax.readyState == 4) {
	if (ajax.status == 200 || ajax.status == 201) {
	    var v = ajax.responseXML;
	    var msg = v.getElementById('status').innerText;
	    var h = document.getElementById('querystatus');
	    h.innerHTML = msg;
	}
    }
}

function send(e) {
    var canvas = document.getElementById('canvas');
    if (window.FormData) {
	canvasToBlob(canvas, function(ee) {
	    if (ee) {
		var fd = new FormData(e);
		fd.append('mode', 'post');
		fd.append('canvas', ee);
		ajax.open('post', e.action, true);
		ajax.onreadystatechange = getter;
		ajax.responseType = 'document';
		ajax.setRequestHeader("Pragma", "no-cache");
		ajax.setRequestHeader("Cache-Control", "no-cache");
		ajax.setRequestHeader("If-Modified-Since", "Thu, 01 Jun 1970 00:00:00 GMT");
		ajax.send(fd);
	    }
	}, 'image/png');
    }
}

function draw(e) {
    if (!downFlag || !(e.buttons == 1 || e.buttons == 3)) return;
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');
    var xnow = e.clientX;
    var ynow = e.clientY;
    if (firstDownFlag == 1) {
	x1 = downX;
	y1 = downY;
        x2 = x3 = xnow;
	y2 = y3 = ynow;
	firstDownFlag = 2;
    } else {
	x3 = x2;
	y3 = y2;
	x2 = x1;
	y2 = y1;
	x1 = xnow;
	y1 = ynow;
    }
    var x1a = x1 - canvas.offsetLeft;
    var y1a = y1 - canvas.offsetTop;
    var x2a = x2 - canvas.offsetLeft;
    var y2a = y2 - canvas.offsetTop;
    var x3a = x3 - canvas.offsetLeft;
    var y3a = y3 - canvas.offsetTop;
    context.strokeStyle = 'black';
    context.lineWidth = 1;
    if (e.buttons == 3) {
	context.strokeStyle = 'white';
	context.lineWidth = 3;
    }
    context.beginPath();
    context.moveTo(x1a, y1a);
    context.quadraticCurveTo(x2a, y2a, x3a, y3a);
    context.stroke();
    context.closePath();
}

function mousedown(e) {
    downFlag = true;
    firstDownFlag = 1;
    downX = e.clientX;
    downY = e.clientY;
}

function mouseup(e) {
    downFlag = false;
}

window.addEventListener('load', function() {
    var canvas = document.getElementById('canvas');
    canvas.addEventListener('mousemove', draw, true);
    canvas.addEventListener('mousedown', mousedown, true);
    canvas.addEventListener('mouseup', mouseup, true);

    document.getElementById('form').addEventListener('submit', function(e) {
	var submit = document.getElementById('submit');
	submit.disabled = true;
	var form = this;
	e.preventDefault();
	send(form);
    }, false);

    var context = canvas.getContext('2d');
    context.fillStyle = 'rgba(255,255,255,1)';
    context.fillRect(0, 0, canvas.width, canvas.height);
}, true);

// vim: set tabstop=8 softtabstop=4 shiftwidth=4 :
