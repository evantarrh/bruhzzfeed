$().ready(function() {
  $('button').click(function() {
    $.ajax({
      type: 'POST',
      data: 'example=something',
      url: '/new',
      success: function(response){
        window.location.replace(window.location.href + response);
      },
      error: function(response){
        // do nothing lol
      }
    });
  })
});
