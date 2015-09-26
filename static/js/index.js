$().ready(function() {
  $('button').click(function() {
    $.ajax({
      type: 'POST',
      data: 'bogus',
      url: '/new'
    });
  })
});
