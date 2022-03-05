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
var banner = {
    init:function() {
	    banner.initTree();
	    banner.banIP(cookie.get('BANLIST='));
    },
    initTree:function() {
	if (document.getElementById('trad') !== null) {
	    foreachClass('banip', function(e) {
		var d = e.getElementsByClassName('banlink');
		if (d[0].childNodes.length == 0) {
		    var a = document.createElement('a');
		    a.href = '#';
		    a.onclick = function(ee) {
			banner.push(e.attributes.name.value);
			banner.banIP(cookie.get('BANLIST='));
			return false;
		    };
		    d[0].appendChild(a);
		    a.appendChild(document.createTextNode('退'));
		    a.style.marginLeft = '1em';
		    a.title = 'この投稿者を以後表示しない';
		}
	    });
	}
	foreachClass('banmsg', function(e) {
	    var d = e.getElementsByClassName('unban');
	    if (d.length != 0 && d[0].childNodes.length == 0) {
		var a = document.createElement('a');
		a.href = '#';
		a.onclick = function(ee) {
		    banner.pop(e.attributes.name.value);
		    banner.unbanIP(e.attributes.name.value);
		    return false;
		};
		if (d.length !== 0) {
		    d[0].appendChild(a);
		}
		a.appendChild(document.createTextNode('vanish'));
		a.appendChild(document.createElement('br'));
	    }
	});
    },
    banIP:function(list) {
	var a = list.split(':');
	foreachClass('banip', function(e) {
	    for (var i = 0; i < a.length; i++) {
		if (a[i] !== '' && a[i] === e.attributes.name.value) {
		    e.style.display = 'none';
		}
	    }
	});
	foreachClass('banmsg', function(e) {
	    for (var i = 0; i < a.length; i++) {
		if (a[i] !== '' && a[i] === e.attributes.name.value) {
		    e.style.display = '';
		}
	    }
	});
    },
    unbanIP:function(id) {
	foreachClass('banip', function(e) {
	    if (id === e.attributes.name.value) {
		e.style.display = '';
	    }
	});
	foreachClass('banmsg', function(e) {
	    if (id === e.attributes.name.value) {
		e.style.display = 'none';
	    }
	});
    },
    push:function(id) {
	var a = cookie.get('BANLIST=').split(':');
	a.push(id);
	if (a.length > 50) {
	    a.shift();
	}
	cookie.set('BANLIST', a.join(':'));
    },
    pop:function(id) {
	var a = cookie.get('BANLIST=').split(':');
	var d = [];
	for (var i = 0; i < a.length; i++) {
	    if (a[i] !== id) {
		d.push(a[i]);
	    }
	}
	cookie.set('BANLIST', d.join(':'));
    }
};
banner.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
