 $(function() {
   $('SPAN.bookicommentmarker').click(function() {      
	   //   $('SPAN.bookicommentmarker > IMG.markerimage').click(function() {      

      var $this = this;
      var commentID = $($this).attr("id").substr(19);
      //      var commentID = $($this).parent().attr("id").substr(19);


      var d = $('<div class="commentdialog" title="Comments"></div>');
      var s = '';

      $('#bookicomment_'+commentID+' .bookicommententry').each(function(i, v) {
		var content = $('.bookicommentcontent', v).html();
		var author = $('.bookicommentuser', v).html();
		var tme = $('.bookicommentdate', v).html();

		var d = new Date();
		d.setTime(parseInt(tme));
		
		s += '<div class="entry"><div class="header"><b>'+author+'</b> - <i>'+d.toLocaleString()+'</i></div>'+content+'</div>';
      });

      d.append(s);
      d.dialog({
         resizable: true,
         width: 400,
         height: 300,
         modal: false
         /*,
         buttons: [
            {
             text: 'OK',
             click: function() {
                 $(this).dialog('close');
             }
            }
         ] */
      });
   });
 });
