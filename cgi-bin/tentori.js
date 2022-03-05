"use strict";
var tentori = {
    init:function() {
	var pos = document.getElementById('tentori');
	var a = document.createElement('span');
	a.onclick = function(ee) {
	    tentori.update(pos);
	    return false;
	};
	pos.appendChild(a);
	a.appendChild(document.createTextNode(''));
	this.update(pos);
    },
    update:function(pos) {
	var index = Math.floor(Math.random() * 10);
	var req = new XMLHttpRequest();
	req.open('get', 'tentori' + index + '.txt', true);
	req.send(null);
	req.onload = function() {
	    var text = req.responseText;
	    var lines = text.split(/\r\n|\n/);
            var line = lines[Math.floor(Math.random() * lines.length)];
	    pos.childNodes[0].innerHTML = line + '&nbsp;' +
		    tentori.mark[index] + tentori.score[index] + '点';
	}
    },
    mark:['◎', '×', '▲', '▲', '△', '△', '●', '●', '○', '○'],
    score:[10, 1, 2, 3, 4, 5, 6, 7, 8, 9]
};
tentori.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
