/*------------------------------------------*\
 InsertSnippet for Xinha
 _______________________
 
 Insert HTML fragments or template variables
 
\*------------------------------------------*/

function InsertSnippet(editor) {
	this.editor = editor;

	var cfg = editor.config;
	var self = this;
	

	cfg.registerButton({
	id       : "insertsnippet",
	tooltip  : this._lc("Insert Snippet"),
	image    : editor.imgURL("ed_snippet.gif", "InsertSnippet"),
	textMode : false,
	action   : function(editor) {
			self.buttonPress(editor);
		}
	});
	cfg.addToolbarElement("insertsnippet", "insertimage", -1);
	this.snippets = null;
	var backend = cfg.InsertSnippet.snippets + '?';
	
	if(cfg.InsertSnippet.backend_data != null)
    {
    	for ( var i in cfg.InsertSnippet.backend_data )
        {
            backend += '&' + i + '=' + encodeURIComponent(cfg.InsertSnippet.backend_data[i]);
        }
    }
    Xinha._getback(backend,function (getback) {eval(getback); self.snippets = snippets;});
}

InsertSnippet.prototype.onUpdateToolbar = function() {
	if (!this.snippets){
		this.editor._toolbarObjects.insertsnippet.state("enabled", false);
	}
	else InsertSnippet.prototype.onUpdateToolbar = null;
}

InsertSnippet._pluginInfo = {
  name          : "InsertSnippet",
  version       : "1.2",
  developer     : "Raimund Meyer",
  developer_url : "http://x-webservice.net",
  c_owner       : "Raimund Meyer",
  sponsor       : "",
  sponsor_url   : "",
  license       : "htmlArea"
};

InsertSnippet.prototype._lc = function(string) {
    return Xinha._lc(string, 'InsertSnippet');
};

InsertSnippet.prototype.onGenerate = function() {
  this.editor.addEditorStylesheet(Xinha.getPluginDir("InsertSnippet") + '/InsertSnippet.css');
};

Xinha.Config.prototype.InsertSnippet =
{
  'snippets' : Xinha.getPluginDir("InsertSnippet")+"/demosnippets.js", // purely demo purposes, you should change this
  'css' : ['../InsertSnippet.css'], //deprecated, CSS is now pulled from xinha_config
  'showInsertVariable': false,
  'backend_data' : null
};
	
InsertSnippet.prototype.buttonPress = function(editor) {
		var args = editor.config;
			args.snippets = this.snippets;
		var self = this;
		editor._popupDialog( "plugin://InsertSnippet/insertsnippet", function( param ) {
	
		if ( !param ) { 
	      return false;
	    }
				   	   
		
		editor.focusEditor();
		if (param['how'] == 'variable') {
			editor.insertHTML('{'+self.snippets[param["snippetnum"]].id+'}');
		} else {
			editor.insertHTML(self.snippets[param["snippetnum"]].HTML);
	   	}
  
    }, args);
  };