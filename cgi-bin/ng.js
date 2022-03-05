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
var nger = {
    init:function() {
	var f = document.getElementById('ng');
	nger.initNg(f);
	nger.doNg(cookie.get('NGLIST='));
    },
    initNg:function(place) {
	var ng = cookie.get('NGLIST=');
	var visible = false;
	this.visibleExp(true);
	this.ngLink = document.createElement('a');
	this.ngLink.href = '#';
	this.ngLink.onclick = function(e) {
	    nger.ngBox.style.display = visible ? 'none' : '';
	    nger.visibleExp(visible);
	    visible = !visible;
	    return false;
	};
	var text1 = document.createTextNode('NG ' + this.ngCount + '件');
	this.ngLink.appendChild(text1);
	place.appendChild(this.ngLink);
	var ngText = document.createElement('input');
	ngText.size = 64;
	ngText.name = 'ng';
	ngText.value = ng;
	ngText.type = 'text';
	this.ngBox = document.createElement('span');
	this.ngBox.appendChild(ngText);
	this.ngBox.style.display = 'none';
	this.ngUpdate = document.createElement('a');
	this.ngUpdate.href = '#';
	this.ngUpdate.onclick = function(e) {
	    nger.doNg(ngText.value);
	    cookie.set('NGLIST', ngText.value);
	    return false;
	};
	this.ngUpdate.appendChild(document.createTextNode('更新'));
	this.ngBox.appendChild(this.ngUpdate);
	place.appendChild(this.ngBox);
	place.appendChild(document.createTextNode(' '));
    },
    visibleExp:function(visible) {
	if (document.getElementById('exp') !== null) {
	    foreachClass('ngpart', function(e) {
		var d = e.getElementsByClassName('ngexp');
		var a = d[0].getElementsByTagName('a');
		a[0].style.display = visible ? 'none' : '';
	    });
	}
    },
    doNg:function(ng) {
	this.ngCount = 0;
	if (ng !== '') {
	    var ngReg = new RegExp(ng);
	    foreachClass('ngpart', function(e) {
		if (e.innerHTML.search(ngReg) !== -1) {
		    e.style.display = 'none';
		    (nger.ngCount)++;
		}
	    });
	}
	this.ngLink.innerHTML = 'NG ' + this.ngCount + '件';
    },
    ngLink:null,
    ngBox:null,
    ngUpdate:null,
    ngCount:0
};
nger.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
