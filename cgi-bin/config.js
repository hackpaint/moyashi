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

var configs = {
    init:function() {
	var f = document.getElementById('config');
	var visible = false;
	this.settingLink = document.createElement('a');
	this.settingLink.href = '#';
	this.settingLink.onclick = function(e) {
	    configs.settingBox.style.display = visible ? 'none' : '';
	    visible = !visible;
	    return false;
	};
	f.appendChild(this.settingLink);
	this.settingLink.appendChild(document.createTextNode('設定'));
	this.settingBox = document.createElement('div');
	this.settingBox.style.display = 'none';
	this.settingBox.style.margin = '1em';
	this.settingBox.style.marginLeft = '2em';
	configs.initBox(this.settingBox);
	f.appendChild(this.settingBox);
    },
    initBox:function(pos) {
	var name = cookie.get('NAME=');
	var nameInput = document.createElement('input');
	nameInput.size = 40;
	nameInput.name = 'nameinput';
	nameInput.value = name;
	nameInput.type = 'text';
	var display = cookie.get('DISPLAY=');
	var tradc = (display === 'trad') ? true : false;
	var treec = (display === 'tree') ? true : false;
	var expc = (display === '' || display === 'exp') ? true : false;
	var form = document.createElement('form');
	form.id = 'displayform';
	var displayRadio1 = document.createElement('input');
	displayRadio1.id = 'radiotrad';
	displayRadio1.name = 'display';
	displayRadio1.value = 'trad';
	displayRadio1.type = 'radio';
	displayRadio1.checked = tradc;
	var displayRadio2 = document.createElement('input');
	displayRadio2.id = 'radiotree';
	displayRadio2.name = 'display';
	displayRadio2.value = 'tree';
	displayRadio2.type = 'radio';
	displayRadio2.checked = treec;
	var displayRadio3 = document.createElement('input');
	displayRadio3.id = 'radioexp';
	displayRadio3.name = 'display';
	displayRadio3.value = 'exp';
	displayRadio3.type = 'radio';
	displayRadio3.checked = expc;
	var configLink = document.createElement('a');
	configLink.href = '#';
	configLink.onclick = function() {
	    var tradc = document.forms.displayform.radiotrad.checked;
	    var treec = document.forms.displayform.radiotree.checked;
	    var expc = document.forms.displayform.radioexp.checked;
	    var r;
	    r = tradc ? 'trad' : r;
	    r = treec ? 'tree' : r;
	    r = expc ? 'exp' : r;
	    cookie.set('DISPLAY', r);
	    configs.updateName(nameInput.value);
	    cookie.set('NAME', nameInput.value);
	    return false;
	};
	configLink.appendChild(document.createTextNode('更新'));
	var configBox = document.createElement('div');
	configBox.appendChild(document.createTextNode('デフォルトの名前欄　'));
	configBox.appendChild(nameInput);
	configBox.appendChild(document.createTextNode('　'));
	configBox.appendChild(configLink);
	configBox.appendChild(document.createElement('br'));
	form.appendChild(document.createTextNode('表示モード　'));
	form.appendChild(displayRadio1);
	form.appendChild(document.createTextNode('通常　'));
	form.appendChild(displayRadio2);
	form.appendChild(document.createTextNode('ツリー　'));
	form.appendChild(displayRadio3);
	form.appendChild(document.createTextNode('実験　'));
	configBox.appendChild(form);
	pos.appendChild(configBox);
    },
    updateName:function(e) {
	var f = document.getElementById('name');
	f.value = e;
    },
    settingLink:null,
    settingBox:null
};
configs.init();

// vim: set tabstop=8 softtabstop=4 shiftwidth=4 :
