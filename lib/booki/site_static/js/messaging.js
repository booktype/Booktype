(function( $ ){
    
    var methods = {
	init : function( options ) {
	    
	    return this.each(function(){
		    var $this = $(this);
		    var editor_id = Math.floor(Math.random() *100)+1;

		    $(this).data("editor_id", editor_id);

		    $("TEXTAREA.tinyeditor", $this).attr("id", "snippetTextArea"+editor_id);

		    $this.submit(function() {

			    if ($this.find("input[name=attachment]").val())
			    	return true;

			    var formdata = $this.serializeArray();

			    formdata.push({name: "ajax", value: "1"});

			    $("#messages").text("Sending...");

			    $.post(options['view_post'], formdata, function (data) {
				    $("#messages").text(data);
				    setTimeout(function() {
					    $this.closest(".messagefield_dialog").dialog('close');
					}, 2000);
				});
			    return false;
			});
		    
		    
		    $(".myaccordion .myheader", $this).click(function() {
			    $(this).next().slideToggle(600);
			    return false;
			});
		    
		    // ovdje mu ime promjeniti fino
		    $(".expander", $this).click(function() {
			    $("#snippetTextArea"+editor_id, $this).tinymce({script_url : '/site_static/js/tiny_mce/tiny_mce.js',
					theme : "simple"});
			});
		    
		    return true;
		})},
	
	set : function(options) {
	    
	    return this.each(function(){
		    var $this = $(this);

		    $("input[name=content]", $this).val(options['content'] || " ");
		    $("input[name=context_url]", $this).val(options['context_url'] || " ");
		    $("textarea[name=snippet]", $this).val(options['snippet']);

		});
	},

	show : function(options) {
	    return this.each(function(){
		    var $this = $(this);

		    if(options == 'snippet') {
			var editor_id = $this.data("editor_id");
			$("#snippetTextArea"+editor_id, $this).tinymce({script_url : '/site_static/js/tiny_mce/tiny_mce.js',
				    theme : "simple"});

			$("textarea[name=snippet]", $this).closest('div').show();
		    }
		});
	},

	hide : function(options) {
	    return this.each(function(){
		    var $this = $(this);

		    if(options == 'snippet')
			$("textarea[name=snippet]", $this).closest('div').hide();
		});
	}


    };
    
    $.fn.messagefield = function( method ) {
	
	if ( methods[method] ) {
	    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} 
    };


  // when doing it from the editor
  $.bookiMessage = function(snippet) {

    $(".messagefield_dialog").dialog('open');

    values = {"content": '', "context_url": document.location, "snippet": snippet};
    
    $(".messagefield_dialog .messagefield").messagefield('set', values);

    $(".messagefield_dialog .messagefield").messagefield('show', 'snippet');
  };

  $.bookiReply = function(post_dom) {
    var content = $(post_dom).find(".sender").text()+" ";
    var snippet = $(post_dom).find(".snippet").html();
    var context = $(post_dom).find(".context").attr('href');

    if (!snippet) snippet = "";
    if (!context || !snippet) context = "";

    $(".messagefield_dialog").dialog('open');

    values = {"content": content, "context_url": context, "snippet": snippet};
    
    $(".messagefield_dialog .messagefield").messagefield('set', values);

    if(snippet) 
	$(".messagefield_dialog .messagefield").messagefield('show', 'snippet');
    else
	$(".messagefield_dialog .messagefield").messagefield('hide', 'snippet');
  };

    
})( jQuery );



