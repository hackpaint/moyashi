"use strict";
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};
var extender = {
    init:function() {
	var e = document.getElementById('extendparam');
	var v = e.attributes.value.value;
	var p = v.split(',');
	if (p[0] === 'info') {
	    cookie.set('INFO', 'true');
	}
	if (p[0] === 'noinfo') {
	    cookie.set('INFO', 'false');
	}
	var zn = cookie.get('ZYOJINUMBER=');
	if (zn === null) {
	    zn = 0;
	}
	zn++;
	if (zn >= p[1]) {
	    zn = 0;
	}
	cookie.set('ZYOJINUMBER', zn);
    }
};
extender.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
