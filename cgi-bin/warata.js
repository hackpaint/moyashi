"use strict";
function contains(a, e) {
    for (var i = 0; i < a.length; i++) {
	if (a[i] === e) {
	    return true;
	}
    }
    return false;
}
function append(a, e) {
    var d = remove(a, e);
    d.push(e);
    return d;
}
function remove(a, e) {
    var d = [];
    for (var i = 0; i < a.length; i++) {
	if (a[i] !== e) {
	    d.push(a[i]);
	}
    }
    return d;
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
var warater = {
    init:function() {
	cookie.set('WARATAADD', '');
	cookie.set('WARATADEL', '');
	warater.initPage();
    },
    initPage:function() {
	foreachClass('warata', function(e) {
	    var m = e.getElementsByClassName('waratamark');
	    var c = e.getElementsByClassName('waratacount');
	    var i = e.getElementsByClassName('identify');
	    var n = e.attributes.name.value;
	    var v = e.getElementsByClassName('waratalist');
	    var a = document.createElement('span');
	    if(m[0].childNodes.length == 0) {
		m[0].appendChild(a);
		a.appendChild(document.createTextNode('★'));
		a.title = '押せばﾜﾗﾀの星光る';
		a.style.marginLeft = '1em';
		var s = document.createElement('span');
		s.className = 'waratacount';
		a.appendChild(s);
		a.onclick = function() {
		    warater.update(m, c, i, n, v, 1);
		    return false;
		};
		warater.update(m, c, i, n, v, 0);
	    }
	});
    },
    update:function(m, c, i, n, v, f) {
	var wa = cookie.get('WARATAADD=');
	var waa = wa.split(/,/);
	if(waa.length == 1 && waa[0] === '') {
	    waa = [];
	}
	var wd = cookie.get('WARATADEL=');
	var wda = wd.split(/,/);
	if(wda.length == 1 && wda[0] === '') {
	    wda = [];
	}
	var va = v[0].attributes.name.value.split(/:/);
	if(va.length == 1 && va[0] === '') {
	    va = [];
	}
	var t = i[0].attributes.name.value + ':' + n;
	if(f !== 0) {
	    if(contains(va, n)) {
		wda = contains(wda, t) ? remove(wda, t) : append(wda, t);
	    } else {
		waa = contains(waa, t) ? remove(waa, t) : append(waa, t);
	    }
	    cookie.set('WARATAADD', waa.join(','));
	    cookie.set('WARATADEL', wda.join(','));
	}

	var ff = 0;
	if(contains(waa, t)) {
	    ff++;
	}
	if(contains(wda, t)) {
	    --ff;
	}
	m[0].style.cursor = 'pointer';
	ff += va.length;
	m[0].style.color = (contains(waa, t) || (ff >= 0 && contains(va, n))) ? 'red' : 'yellow';
	if(contains(wda, t)) {
	    m[0].style.color = 'yellow';
	}
	c[0].innerHTML = (ff > 0) ? ff : '';
	if(c[0].innerHTML === '') {
	    m[0].style.color = 'white';
	}

    }
};
warater.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
