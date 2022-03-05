$(function($) {
  $('a.zoom').each(function() {
    var w = $(this).children(0).width();
    var h = $(this).children(0).height();
    $(this).mouseenter(function() {
      $(this).css('z-index', '10').children(0).stop().animate({
        'width' : w * 2 + 'px',
        'height' : h * 2 + 'px'
      }, 210);
    });
    $(this).mouseleave(function() {
      $(this).children(0).stop().animate({
        'width' : w + 'px',
        'height' : h + 'px'
      }, 150, function() {
          $(this).css('width', w + 'px').parent.css('z-order', '1');
        }
      );
    });
  });
});
