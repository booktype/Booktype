function BookiSend(editor) {
    this.editor = editor;

    var cfg = editor.config;
    var self = this;
    
    cfg.registerButton({
        id       : "bookisend",
        tooltip  : HTMLArea._lc("Send text snippet"),
        image    : editor.imgURL("ed_image.gif", "BookiSend"),
        textMode : false,

        action   : function(editor) {
	    self.buttonPress(editor);
        }
    });
    cfg.addToolbarElement("bookisend", "inserthorizontalrule", 1);
}

BookiSend._pluginInfo = {
    name          : "Booki Send",
    version       : "1.0",
    developer     : "Booki developers",
    developer_url : "http://www.booki.cc/",
    license       : "none"
};

BookiSend.prototype.buttonPress = function(editor) {
    // XXX adding editor.outwardHtml doesn't work
    if (editor.hasSelectedText())
        $.bookiMessage(editor.getSelectedHTML());
    else
        $.bookiMessage(editor.getHTML());
}
