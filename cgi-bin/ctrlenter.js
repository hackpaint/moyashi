"use strict";
var ctrlenter = {
    init:function() {
	document.getElementById("msgflip").onkeydown = function(e) {
	    if (e.keyCode == 13 && e.ctrlKey) {
		document.getElementById("submitflip").click();
		return false;
	    }
	};
//	document.getElementById("msgflop").onkeydown = function(e) {
//	    if (e.keyCode == 13 && e.ctrlKey) {
//		document.getElementById("submitflop").click();
//		return false;
//	    }
//      };
    }
};
ctrlenter.init();

// vim: tabstop=8 softtabstop=4 shiftwidth=4 textwidth=78 :
