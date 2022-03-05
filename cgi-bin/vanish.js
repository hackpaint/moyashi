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
var vanisher = {
    init:function() {
	vanisher.initTree();
	vanisher.doVanish(cookie.get('VANISHLIST='));
    },
    initTree:function() {
	if (document.getElementById('tree') !== null) {
	    foreachClass('vanishpart', function(e) {
		var d = e.getElementsByClassName('vanishtree');
		if (d[0].childNodes.length == 0) {
		    var a = document.createElement('a');
		    a.href = '#';
		    a.onclick = function(ee) {
			e.style.display = 'none';
			vanisher.push(e.id);
			return false;
		    };
		    d[0].appendChild(a);
		    a.appendChild(document.createTextNode('消'));
		    a.style.marginLeft = '1em';
		    a.title = 'このツリーを以後表示しない';
		}
	    });
	} else if (document.getElementById('exp') !== null) {
	    foreachClass('vanishpart', function(e) {
		var d = e.getElementsByClassName('vanishexp');
		if (d[0].childNodes.length == 0) {
		    var a = document.createElement('a');
		    a.href = '#';
		    a.onclick = function(ee) {
			e.style.display = 'none';
			vanisher.push(e.id);
			return false;
		    };
		    d[0].appendChild(a);
		    a.appendChild(document.createTextNode('消'));
		    a.style.marginLeft = '1em';
		    a.title = 'このツリーを以後表示しない';
		}
	    });
	} else if (document.getElementById('trad') !== null) {
	    foreachClass('vanishpart', function(e) {
		var d = e.getElementsByClassName('vanishtrad');
		if (d[0].childNodes.length == 0) {
		    var a = document.createElement('a');
		    a.href = '#';
		    a.onclick = function(ee) {
			e.style.display = 'none';
			vanisher.push(e.id);
			return false;
		    };
		    d[0].appendChild(a);
		    a.appendChild(document.createTextNode('消'));
		    a.style.marginLeft = '1em';
		    a.title = 'この書き込みを以後表示しない';
		}
	    });
	}
    },
    doVanish:function(list) {
	var a = list.split(':');
	foreachClass('vanishpart', function(e) {
	    for (var i = 0; i < a.length; i++) {
		if (a[i] !== '' && a[i] === e.id) {
		    e.style.display = 'none';
		}
	    }
	});
    },
    push:function(id) {
	var a = cookie.get('VANISHLIST=').split(':');
	a.push(id);
	if (a.length > 50) {
	    a.shift();
	}
	cookie.set('VANISHLIST', a.join(':'));
    }
};
vanisher.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
