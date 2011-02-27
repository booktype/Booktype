// Unormat plugin for Xinha


UnFormat._pluginInfo = {
  name          : "UnFormat",
  version       : "1.0",
  license       : "htmlArea"
};


function UnFormat(editor) {
  this.editor = editor;
  var cfg = editor.config;
  var self = this;

  cfg.registerButton({
    id       : "unformat",
    tooltip  : Xinha._lc("Page Cleaner",'UnFormat'),
    image    : editor.imgURL("unformat.gif", "UnFormat"),
    textMode : false,
    action   : function(editor) {
                 self.show();
               }
  });

  cfg.addToolbarElement("unformat", "killword", 1);
}

UnFormat.prototype.onGenerateOnce = function(editor){
  // Load assets
  var self = UnFormat;
  if (self.loading) return;
  self.loading = true;
  self.methodsReady = true;
  Xinha._getback(Xinha.getPluginDir('UnFormat') + '/dialog.html', function(getback) { self.html = getback; self.dialogReady = true; });
}
UnFormat.prototype.onUpdateToolbar = function(editor){
  if (!(UnFormat.dialogReady && UnFormat.methodsReady))
  {
    this.editor._toolbarObjects.UnFormat.state("enabled", false);
  }
  else this.onUpdateToolbar = null;

}
UnFormat.prototype.prepareDialog = function(editor){
  var self = this;
  var editor = this.editor;

  var dialog = this.dialog = new Xinha.Dialog(editor, UnFormat.html, 'Xinha',{width:400})
  // Connect the OK and Cancel buttons
  dialog.getElementById('ok').onclick = function() {self.apply();}
  dialog.getElementById('cancel').onclick = function() { self.dialog.hide()};
  
  this.dialogReady = true;
}
UnFormat.prototype.show = function(editor){
 if (!this.dialog) this.prepareDialog();

  var editor = this.editor;

  var values = 
  {
    "cleaning_area"    : 'selection',
    "formatting"       : '',
    "html_all"         : ''
  }
  // now calling the show method of the Xinha.Dialog object to set the values and show the actual dialog
  this.dialog.show(values);
  this.dialog.onresize();
}
UnFormat.prototype.apply = function(editor){
  var editor = this.editor;
  var doc = editor._doc;
  var param = this.dialog.getValues();
  
  // selection is only restored on dialog.hide()
  this.dialog.hide();
  // assign the given arguments
  
  if (param["cleaning_area"] == "all") {
    var html = editor._doc.body.innerHTML;
  } else {
    var html = editor.getSelectedHTML();
  }

  if (param.html_all) {
    html = html.replace(/<[\!]*?[^<>]*?>/g, "");
  }

  if (param.formatting) {
    html = html.replace(/style="[^"]*"/gi, "");
    html = html.replace(/<\/?font[^>]*>/gi,"");
    html = html.replace(/<\/?b>/gi,"");
    html = html.replace(/<\/?strong[^>]*>/gi,"");
    html = html.replace(/<\/?i>/gi,"");
    html = html.replace(/<\/?em[^>]*>/gi,"");
    html = html.replace(/<\/?u[^>]*>/gi,"");
    html = html.replace(/<\/?strike[^>]*>/gi,"");
    html = html.replace(/ align=[^\s|>]*/gi,"");
    html = html.replace(/ class=[^\s|>]*/gi,"");
  }
  if (param["cleaning_area"] == "all") {
    editor._doc.body.innerHTML = html;
  } else {
    editor.insertHTML(html);
  }
};
