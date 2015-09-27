$().ready(function() {
  var categories = [];

  $('.bruh').mouseenter(function(event){
    $(event.currentTarget).html("Take a chance");
  });
  $('.bruh').mouseleave(function(event){
    $(event.currentTarget).html("BruhzzFeed");
  });

  $('.submit').click(function(event) {
    if (categories.length === 0) {
      $(event.currentTarget).html('choose some categories ya dingus');
      return;
    }
    $(event.currentTarget).html('ok be patient...');
    var patience = 'ok be patient...'
    setInterval(function(){
      var patienceIndex = patience.indexOf('patient');
      patience = patience.slice(0, patienceIndex) + ' very ' + patience.slice(patienceIndex);
      $(event.currentTarget).html(patience);
    }, 2500);
    $.ajax({
      type: 'POST',
      data: formatCategories(categories),
      url: '/new',
      success: function(response){
        window.location.href = window.location.href + response;
      },
      error: function(response){
        // do nothing lol
      }
    });
  });

  var formatCategories = function (array) {
   var str = "categories=";
   array.forEach(function(val){
    str += val + ',';
   });
   return str;
  };

  $( '.buttons > li > div' ).click(function(event) {
    if($('button').html() == 'choose some categories ya dingus') {
      $('button').html('go!');
    }

    var category = $(event.currentTarget);
    var listItem = category.parent();

    if (listItem.hasClass('selected')){
     listItem.removeClass('selected');
     var index = categories.indexOf(category.html());
     if (index > -1){
      categories.splice(index, 1);
     }
    } else {
     listItem.addClass('selected');
     categories.push(category.html());
    }
     // push to categories
    console.log(categories);

  });
  $( '.buttons > li ' ).mouseenter(function(event) {
    if($(event.currentTarget).hasClass('selected')){
      $(event.currentTarget).addClass('close');
    }
  });
  $( '.buttons > li ' ).mouseleave(function(event) {
    if($(event.currentTarget).hasClass('close')){
      $(event.currentTarget).removeClass('close');
    }
  });
});
