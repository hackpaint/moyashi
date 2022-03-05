"use strict";
function contains(a, e) {
    for (var i = 0; i < a.length; i++) {
	if (a[i] === e) {
	    return true;
	}
    }
    return false;
}
function equals(l, r) {
    return (l === r) ? true : false;
}
function foreach(a, f) {
    var terminator = Object();
    for (var i = 0; i < a.length; i++) {
	if (f(a[i]) === terminator) {
	    break;
	}
    }
}
function foreachClass(c, f) {
    var n = document.getElementsByClassName(c);
    foreach(n, f);
}
function foreachTag(t, f) {
    var n = document.getElementsByTagName(t);
    foreach(n, f);
}
function foreachTagWithClass(t, c, f) {
    var n = c instanceof Array ? contains : equals;
    foreachTag(t, function(e) {
	if (n(c, e.className)) {
	    return f(e);
	}
    });
}
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};
var reloader = {
    init:function() {
	var e = document.getElementById('lastreload');
	var v = e.attributes.value.value;
	cookie.set('LASTRELOAD', v);
    }
};
reloader.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
