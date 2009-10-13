function BookiInsert(editor) {
    this.editor = editor;

    var cfg = editor.config;
    var self = this;
    
    cfg.registerButton({
        id       : "bookiinsert",
        tooltip  : HTMLArea._lc("Insert image"),
        image    : editor.imgURL("ed_image.gif", "BookiInsert"),
        textMode : false,

        action   : function(editor) {
	    self.buttonPress(editor);
        }
    });

    cfg.addToolbarElement("bookiinsert", "inserthorizontalrule", 1);

    
    BookiInsert._pluginInfo = {
	name          : "MyTest",
	version       : "1.0",
	developer     : "David Colliver",
	developer_url : "http://www.revilloc.com/",
	sponsor       : "MyLocalFOCUS.com",
	sponsor_url   : "http://www.MyLocalFOCUS.com/",
	c_owner       : "David Colliver",
	license       : "none"
    };
    
    
    BookiInsert.prototype.buttonPress = function(editor) {
	$("#insertattachment").dialog("open");
    }
    
}