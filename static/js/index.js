$().ready(function() {
  var categories = [];

  $('.submit').click(function() {
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
    var category = $(event.currentTarget);

    if (category.hasClass('selected')){
     category.removeClass('selected');
     var index = categories.indexOf(category.html());
     if (index > -1){
      categories.splice(index, 1);
     }
    } else {
     category.addClass('selected');
     categories.push(category.html());
    }
     // push to categories
    console.log(categories);

   }
  );
});
