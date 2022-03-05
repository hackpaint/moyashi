"use strict";
var isIE = document.all ? true : false;
var terminator = Object();
function foreach(a, f) {
    for (var i = 0; i < a.length; i++) {
		if (f(a[i]) === terminator) {
			break;
		}
    }
}
function foreachTag(t, f) {
    var n = document.getElementsByTagName(t);
    foreach(n, f);
}
var cookie = {
    get:function(n, m) { return (m = ('; ' + document.cookie + ';').match('; ' + n + '(.*?);')) ? decodeURIComponent(m[1]) : ''; },
    set:function(n, v) { document.cookie = n + '=' + encodeURIComponent(v) + '; expires=Mon, 31-Dec-2029 23:59:59 GMT'; }
};
var picture = {
	init:function() {
		var f = document.getElementById('picture');
		var visible = false;
		this.settingLink = document.createElement('a');
		this.settingLink.href = '#';
		this.settingLink.onclick = function(e) {
			picture.settingBox.style.display = visible ? 'none' : '';
			visible = !visible;
			return false;
		};
		f.appendChild(this.settingLink);
		this.settingLink.appendChild(document.createTextNode('画像設定'));
		this.settingBox = document.createElement('div');
		this.settingBox.style.display = 'none';
		this.settingBox.style.margin = '1em';
		this.settingBox.style.marginLeft = '2em';
		
		picture.initThumbnail(this.settingBox);
		f.appendChild(this.settingBox);
	},
	initThumbnail:function(place) {
		var thumbSize = cookie.get('THUMBSIZE=');
		var thumbText = document.createElement('input');
		thumbText.size = 10;
		thumbText.name = 'thumbsize';
		thumbText.value = thumbSize;
		thumbText.type = 'text';
		var popSize = cookie.get('POPSIZE=');
		var popText = document.createElement('input');
		popText.size = 10;
		popText.name = 'popsize';
		popText.value = popSize;
		popText.type = 'text';
		var thumbLink = document.createElement('a');
		thumbLink.href = '#';
		thumbLink.onclick = function() {
			picture.update(thumbText.value, popText.value);
			cookie.set('THUMBSIZE', thumbText.value);
			cookie.set('POPSIZE', popText.value);
			return false;
		};
		thumbLink.appendChild(document.createTextNode('更新'));
		var thumbBox = document.createElement('div');
		thumbBox.appendChild(document.createTextNode('サムネイルサイズ'));
		thumbBox.appendChild(thumbText);
		thumbBox.appendChild(document.createTextNode('　'));
		thumbBox.appendChild(document.createTextNode('ポップアップサイズ'));
		thumbBox.appendChild(popText);
		thumbBox.appendChild(document.createTextNode('　'));
		thumbBox.appendChild(thumbLink);
		place.appendChild(thumbBox);
		picture.update(thumbText.value, popText.value);
	},
	update:function(s1, s2) {
		picture.thumbSize = s1;
		picture.popSize = s2;
		picture.initThumb();
		foreachTag('img', function(node) {
			if (node.className === 'thumb') {
				if (s1 === 0) {
					node.parentNode.style.display = 'none';
				} else {
					node.parentNode.style.display = '';
				}
				picture.setImageSize(node, s1);
			} else if (node.className === 'pop') {
				picture.setImageSize(node, s2);
			}
		});
	},
	setImageSize:function(n, s) {
		n.width = s;
		n.style.width = s;
		n.style.maxWidth = s;
	},
	initThumb:function() {
		if (!picture.initialized && picture.thumbSize > 0) {
			picture.apply();
			picture.initialized = true;
		}
	},
	apply:function() {
		var regex = /^http.?:\/\/(.*)(\.jpg|\.jpeg|\.gif|\.png)$/i;
		var skip = false;
		foreachTag('a', function(node) {
			if (node.href.match(regex)) {
				if (skip) {
					skip = false;
					return;
				}
				var thumb = node.cloneNode(false);
				var img1 = document.createElement('img');
				img1.src = node.href;
				img1.className = 'thumb';
				picture.setImageSize(img1, picture.thumbSize);
				thumb.appendChild(img1);
				if (picture.popSize !== 0) {
					(function() {
						var initialized_ = false;
						var p = null;
						thumb.onmouseover = function() {
							if (initialized_) {
								p.style.display = '';
								return;
							}
							p = document.createElement('a');
							var img2 = document.createElement('img');
							img2.src = thumb.childNodes[0].src;
							picture.setImageSize(img2, picture.popSize);
							img2.className = 'pop';
							p.appendChild(img2);
							p.appendChild(document.createElement('br'));
							p.appendChild(document.createTextNode(thumb.childNodes[0].src));
							p.href = thumb.childNodes[0].src;
							p.target = thumb.childNodes[0].target;
							p.style.backgroundColor = '#004040';
							p.style.border = '1px dashed #008080';
							p.style.padding = '2px';
							p.style.fontSize = '80%';
							p.style.position = 'absolute';
							p.style.top = thumb.offsetTop;
							p.style.left = thumb.offsetLeft;
							p.onmouseout = function() {
								p.style.display = 'none';
							};
							p.onmouseover = function() {
								p.style.display = '';
							};
							thumb.appendChild(p);
							initialized_ = true;
						};
						thumb.onmouseout = function() {
							p.style.display = 'none';
						};
					})();
				}
				var holder = document.createElement('span');
				holder.appendChild(thumb);
				holder.appendChild(document.createElement('br'));
				node.parentNode.insertBefore(holder, node);
				skip = true;
			}
		});
	},
	settingLink:null,
	settingBox:null,
	initialized:false,
	thumbSize:0,
	popSize:0
};
picture.init();
