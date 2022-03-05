"use strict";
var newer = {
    init:function() {
	if (window.XMLHttpRequest) {
	    this.req = new XMLHttpRequest();
	} else {
	    this.req = new ActiveXObject("Microsoft.XMLHTTP");
	}
	setTimeout("newer.reloader()", 60000);
    },
    create:function(v) {
	if (!this.created) {
	    var i = document.getElementById('newerline');
	    var d = document.createElement('div');
	    d.style.textAlign = 'center';
	    d.appendChild(document.createTextNode('楽しい書き込みが '));
	    var s = document.createElement('span');
	    s.id = 'newervalue';
	    s.appendChild(document.createTextNode(v));
	    d.appendChild(s);
	    d.appendChild(document.createTextNode(' 件あります。'));
	    d.addEventListener('mousedown', function(e) {
		document.getElementById('submitflip').click();
		return false;
	    }, false);
	    i.appendChild(d);
	    this.created = true;
	}
    },
    reloader:function() {
	var l = document.getElementById('lastreload');
	var v = l.attributes.value.value;
	this.req.open("GET", "bbs.cgi?newerdisp=" + v, true);
	this.req.onreadystatechange = newergetter;
	this.req.responseType = "document";
	this.req.setRequestHeader("Pragma", "no-cache");
	this.req.setRequestHeader("Cache-Control", "no-cache");
	this.req.setRequestHeader("If-Modified-Since", "Thu, 01 Jun 1970 00:00:00 GMT");
	this.req.send(null);
	setTimeout("newer.reloader()", 60000);
    },
    getter:function() {
	if (this.req.readyState == 4) {
	    if (this.req.status == 200 || this.req.status == 201) {
		var v = this.req.responseXML;
		var c = v.getElementById('newercount');
		var cc = c.attributes.value.value;
		if (cc > 0) {
		    newer.create(cc);
		    var e = document.getElementById('newervalue');
		    e.innerHTML = cc;
		    newer.titler(cc);
		}
	    }
	}
    },
    titler:function(n) {
	var v = document.title;
	if (v.charAt(0) == '(') {
	    var t = v.substring(v.lastIndexOf(')') + 2);
	    document.title = '(' + n + ') ' + t;
	} else {
	    document.title = '(' + n + ') ' + v;
	}
    },
    created:false,
    req:null
};
newer.init();
function newergetter() {
    newer.getter();
}

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
