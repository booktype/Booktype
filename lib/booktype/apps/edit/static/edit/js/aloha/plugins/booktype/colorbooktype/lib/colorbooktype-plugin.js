  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera) {
	  		var $a = null;
	  		var range = null;
	  		var editable = null;

  var aaColor = [
    ['#000000', '#424242', '#636363', '#9C9C94', '#CEC6CE', '#EFEFEF', '#EFF7F7', '#FFFFFF'],
    ['#FF0000', '#FF9C00', '#FFFF00', '#00FF00', '#00FFFF', '#0000FF', '#9C00FF', '#FF00FF'],
    ['#F7C6CE', '#FFE7CE', '#FFEFC6', '#D6EFD6', '#CEDEE7', '#CEE7F7', '#D6D6E7', '#E7D6DE'],
    ['#E79C9C', '#FFC69C', '#FFE79C', '#B5D6A5', '#A5C6CE', '#9CC6EF', '#B5A5D6', '#D6A5BD'],
    ['#E76363', '#F7AD6B', '#FFD663', '#94BD7B', '#73A5AD', '#6BADDE', '#8C7BC6', '#C67BA5'],
    ['#CE0000', '#E79439', '#EFC631', '#6BA54A', '#4A7B8C', '#3984C6', '#634AA5', '#A54A7B'],
    ['#9C0000', '#B56308', '#BD9400', '#397B21', '#104A5A', '#085294', '#311873', '#731842'],
    ['#630000', '#7B3900', '#846300', '#295218', '#083139', '#003163', '#21104A', '#4A1031']
  ];	  		
					        	
  			return Plugin.create('colorbooktype', {
		        init: function () {

				 jQuery19("#newLink BUTTON.btn-primary").on('click', function() {
						var title = jQuery19("#newLink INPUT[name=title]").val();
	   					var url = jQuery19("#newLink INPUT[name=url]").val();

	   					if(jQuery19.trim(title) !== '' && jQuery19.trim(url) !== '') {

						    if($a == null) {
	                          	$a = jQuery('<a/>').prop('href', url).text(title);

	                          	// A BIT DIFFERENT IF IS COLLAPSED
					//            if (range.isCollapsed()) {

	   							GENTICS.Utils.Dom.removeRange(range);
	   		                    GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
	   		                } else 
    					    	$a.prop('href', url).text(title);

							range.select();
		                	jQuery19('#newLink').modal('hide');
		            	}
		            });

				   UI.adopt('color', null, {
				      click: function() {
				      	        editable = Aloha.activeEditable;
						        range = Aloha.Selection.getRangeObject();
						        jQuery19('#colorDialog DIV.modal-body').empty();

						        var s = '';
						        for(var i=0; i<aaColor.length;i++) {
						        	for(var j=0; j<aaColor[i].length; j++) {
						        		s += '<button class="bt-color" data-color="'+aaColor[j][i]+'" style="float: left; margin: 5px; width: 20px; height: 20px; background-color: '+aaColor[j][i]+'"></button>';
						        	}
						        	s += '<div style="clear: both"/>';
						        }
						        jQuery19('#colorDialog DIV.modal-body').append(s);

                                jQuery19('#colorDialog DIV.modal-body BUTTON.bt-color').on('click', function() {
                                    var color = jQuery19(this).attr("data-color");
                                    console.log(color);
                                    GENTICS.Utils.Dom.addMarkup(range, jQuery('<span style="color: '+color+'"></span>'), false);
                                    range.select();
                                    jQuery19('#colorDialog').modal('hide');
                                    //jQuery19('DIV.btn-toolbar BUTTON.color').css("color", color);
                                    return false;
                                });
   	      	                    jQuery19('#colorDialog').modal('show');
				      }
				  });		            
		        }
		    });

  		}
);