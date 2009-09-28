/** htmlArea - James' Fork - Linker Plugin **/
Linker._pluginInfo =
{
  name     : "Linker",
  version  : "1.0",
  developer: "James Sleeman",
  developer_url: "http://www.gogo.co.nz/",
  c_owner      : "Gogo Internet Services",
  license      : "htmlArea",
  sponsor      : "Gogo Internet Services",
  sponsor_url  : "http://www.gogo.co.nz/"
};

Xinha.loadStyle('dTree/dtree.css', 'Linker');

Xinha.Config.prototype.Linker =
{
  'treeCaption' : document.location.host,
  'backend' : Xinha.getPluginDir("Linker") + '/scan.php',
  'backend_data' : null,
  'files' : null
};


function Linker(editor, args)
{
  this.editor  = editor;
  this.lConfig = editor.config.Linker;

  var linker = this;
  if(editor.config.btnList.createlink)
  {
    editor.config.btnList.createlink[3]
      =  function(e, objname, obj) { linker._createLink(linker._getSelectedAnchor()); };
  }
  else
  {
    editor.config.registerButton(
                                 'createlink', 'Insert/Modify Hyperlink', [_editor_url + "images/ed_buttons_main.gif",6,1], false,
                                 function(e, objname, obj) { linker._createLink(linker._getSelectedAnchor()); }
                                 );
  }

  // See if we can find 'createlink'
 editor.config.addToolbarElement("createlink", "createlink", 0);
}

Linker.prototype._lc = function(string)
{
  return Xinha._lc(string, 'Linker');
};


Linker.prototype.onGenerateOnce = function()
{
  Linker.loadAssets();
  this.loadFiles();
};

Linker.prototype.onUpdateToolbar = function()
{ 
  if (typeof dTree == 'undefined' || !Linker.methodsReady || !Linker.html || !this.files)
  {
    this.editor._toolbarObjects.createlink.state("enabled", false);
  }
  else this.onUpdateToolbar = null;
};

Linker.Dialog_dTrees = [ ];

Linker.loadAssets = function()
{
  var self = Linker;
  if (self.loading) return;
  self.loading = true;
  Xinha._getback(Xinha.getPluginDir("Linker") + '/pluginMethods.js', function(getback) { eval(getback); self.methodsReady = true; });
  Xinha._loadback( Xinha.getPluginDir("Linker") + '/dTree/dtree.js', function() {Linker.dTreeReady = true; } );
  Xinha._getback( Xinha.getPluginDir("Linker") + '/dialog.html', function(getback) { self.html = getback; } );
}

Linker.prototype.loadFiles = function()
{
    var linker = this;
    if(linker.lConfig.backend)
    {
        //get files from backend
        Xinha._postback(linker.lConfig.backend,
                          linker.lConfig.backend_data,
                          function(txt) {
                            try {
                                linker.files = eval(txt);
                            } catch(Error) {
                                linker.files = [ {url:'',title:Error.toString()} ];
                            }
                            });
    }
    else if(linker.lConfig.files != null)
    {
        //get files from plugin-config
        linker.files = linker.lConfig.files;
    }
}
