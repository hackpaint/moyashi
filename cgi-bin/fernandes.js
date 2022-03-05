"use strict";
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};
var fernandes = {
    init:function() {
	var v = document.getElementById("fernandes");
	var d = document.createElement("span");
	d.id = "fernandesnorm";
	d.style.display = "inline";
	d.addEventListener("mouseover", function(e) {
	    var f1 = document.getElementById("fernandesnorm");
	    f1.style.display = "none";
	    var f2 = document.getElementById("fernandesexcl");
	    var f3 = document.getElementById("fernandesnote");
	    var f4 = document.getElementById("fernandesslee");
	    var f5 = document.getElementById("fernandesques");
	    switch (fernandes.scene) {
		case 0:
		    f2.style.display = "inline";
		    fernandes.scene++;
		    break;
		case 1:
		    f3.style.display = "inline";
		    fernandes.scene++;
		    break;
		case 2:
		    f4.style.display = "inline";
		    fernandes.scene++;
		    break;
		case 3:
		    f5.style.display = "inline";
		    fernandes.scene = 0;
	    }
	    setTimeout(function() {
		f1.style.display = "inline";
		f2.style.display = "none";
		f3.style.display = "none";
		f4.style.display = "none";
		f5.style.display = "none";
	    }, 1000);
	}, false);
	fernandes.fliplinkline();
	fernandes.fliplinkline();
	fernandes.initlinkline();
	d.addEventListener("dblclick", function(e) {
	    fernandes.fliplinkline();
	    fernandes.initlinkline();
	});
//	d.appendChild(document.createTextNode("　∧∧∧∧"));
//	d.appendChild(document.createElement("br"));
//	d.appendChild(document.createTextNode("　(~~)('')"));
	d.appendChild(document.createTextNode("　 ∧∧"));
	d.appendChild(document.createElement("br"));
	d.appendChild(document.createTextNode("　(~~ )～"));
	v.appendChild(d);
	var g = document.createElement("span");
	g.id = "fernandesexcl";
	g.style.display = "none";
	g.addEventListener("dblclick", function(e) {
	    fernandes.fliplinkline();
	    fernandes.initlinkline();
	});
//	g.appendChild(document.createTextNode("　　!"));
//	g.appendChild(document.createElement("br"));
//	g.appendChild(document.createTextNode("　∧∧∧∧"));
//	g.appendChild(document.createElement("br"));
//	g.appendChild(document.createTextNode("　(ﾟﾟ)('')"));
	g.appendChild(document.createTextNode("　　　!"));
	g.appendChild(document.createElement("br"));
	g.appendChild(document.createTextNode("　 ∧∧"));
	g.appendChild(document.createElement("br"));
	g.appendChild(document.createTextNode("　(ﾟﾟ )ー"));
	v.appendChild(g);
	var h = document.createElement("span");
	h.id = "fernandesnote";
	h.style.display = "none";
	h.addEventListener("dblclick", function(e) {
	    fernandes.fliplinkline();
	    fernandes.initlinkline();
	});
//	h.appendChild(document.createTextNode("　　♪"));
//	h.appendChild(document.createElement("br"));
//	h.appendChild(document.createTextNode("　∧∧∧∧"));
//	h.appendChild(document.createElement("br"));
//	h.appendChild(document.createTextNode("　(^^)('')"));
	h.appendChild(document.createTextNode("　　　♪"));
	h.appendChild(document.createElement("br"));
	h.appendChild(document.createTextNode("　 ∧∧"));
	h.appendChild(document.createElement("br"));
	h.appendChild(document.createTextNode("　(^^*)～\""));
	v.appendChild(h);
	var j = document.createElement("span");
	j.id = "fernandesslee";
	j.style.display = "none";
	j.addEventListener("dblclick", function(e) {
	    fernandes.fliplinkline();
	    fernandes.initlinkline();
	});
	j.appendChild(document.createTextNode("　　　zz"));
	j.appendChild(document.createElement("br"));
	j.appendChild(document.createTextNode("　 ∧∧"));
	j.appendChild(document.createElement("br"));
	j.appendChild(document.createTextNode("　(-- )～"));
	v.appendChild(j);
	var k = document.createElement("span");
	k.id = "fernandesques";
	k.style.display = "none";
	k.addEventListener("dblclick", function(e) {
	    fernandes.fliplinkline();
	    fernandes.initlinkline();
	});
	k.appendChild(document.createTextNode("　　　？"));
	k.appendChild(document.createElement("br"));
	k.appendChild(document.createTextNode("　 ∧∧"));
	k.appendChild(document.createElement("br"));
	k.appendChild(document.createTextNode("　(‥ )～"));
	v.appendChild(k);
    },
    initlinkline:function() {
	var f = cookie.get('LINKLINE=');
	var v = document.getElementById("linklines");
	v.style.display = f;
    },
    fliplinkline:function() {
	var f = cookie.get('LINKLINE=');
	f = (f == '' || f == 'inline') ? 'none' : 'inline';
	cookie.set('LINKLINE', f);
    },
    scene:0
};
fernandes.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
