"use strict";
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};
var zoomer = {
    init:function() {
	if (document.getElementById('smartphone') !== null) return;
	var d = document.getElementById('zoomer');
	zoomer.initCookie();
	var lhs = document.createElement('span');
	lhs.appendChild(document.createTextNode('<小'));
	var cnt = document.createElement('span');
	cnt.appendChild(document.createTextNode('中'));
	var rhs = document.createElement('span');
	rhs.appendChild(document.createTextNode('大>'));
	lhs.addEventListener('mousedown', function(e) {
	    var z = cookie.get('ZOOM=');
	    if (z > 1) {
		--z;
	    }
	    cookie.set('ZOOM', z);
	    var s = document.getElementById('shadow');
	    zoomer.setZoom(s, z);
	    return false;
	}, false);
	cnt.addEventListener('mousedown', function(e) {
	    cookie.set('ZOOM', 1 / 0.25);
	    var s = document.getElementById('shadow');
	    zoomer.setZoom(s, 1 / 0.25);
	    return false;
	}, false);
	rhs.addEventListener('mousedown', function(e) {
	    var z = cookie.get('ZOOM=');
	    if (10 > z) {
		z++;
	    }
	    cookie.set('ZOOM', z);
	    var s = document.getElementById('shadow');
	    zoomer.setZoom(s, z);
	    return false;
	}, false);
	lhs.style.cursor = 'pointer';
	cnt.style.cursor = 'pointer';
	rhs.style.cursor = 'pointer';
	d.appendChild(document.createTextNode('文字サイズ:'));
	d.appendChild(lhs);
	d.appendChild(cnt);
	d.appendChild(rhs);
    },
    initCookie:function() {
	var z = cookie.get('ZOOM=');
	if (z === '') {
	    z = 1 / 0.25;
	}
	cookie.set('ZOOM', z);
	var s = document.getElementById('shadow');
	s.style.zoom = z * 0.25;
    },
    setZoom:function(e, z) {
	e.style.zoom = z * 0.25;
    }
};
zoomer.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
