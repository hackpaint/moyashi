"use strict";
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};

var tinyflipper = {
    init:function() {
	var v = document.getElementById('boardtitle');
	v.addEventListener('mousedown', function(e) {
	    tinyflipper.flipVisible();
	    tinyflipper.setVisible();
	});
	tinyflipper.setVisible();
    },
    setVisible:function() {
	var v = document.getElementById('tinyflip');
	var disp = cookie.get('TINYFLIP=');
	disp = (disp == '') ? 'inline' : disp;
	v.style.display = disp;
	var o = document.getElementById('tinyflop');
//	o.style.display = (disp == 'inline') ? 'none' : 'inline';
    },
    flipVisible:function() {
	var disp = cookie.get('TINYFLIP=');
	disp = (disp == '' || disp == 'inline') ? 'none' : 'inline';
	cookie.set('TINYFLIP', disp);
    }
};
tinyflipper.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
