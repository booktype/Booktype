// Filter plugin for Xinha
// Implementation by Udo Schmal & Schaffrath NeueMedien
// Original Author - Udo Schmal
//
// (c) Udo Schmal & Schaffrath NeueMedien 2004
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).
function Filter(editor) {
  this.editor = editor;
  var cfg = editor.config;
  var self = this;
  // register the toolbar buttons provided by this plugin
  cfg.registerButton({
    id: "filter",
    tooltip  : this._lc("Filter"),
    image    : editor.imgURL("ed_filter.gif", "Filter"),
    textMode : false,
    action   : function(editor) {
                 self.buttonPress(editor);
               }
  });
  if (!cfg.Filters)
    cfg.Filters = ["Paragraph","Word"];
  for (var i = 0; i < editor.config.Filters.length; i++) {
    self.add(editor.config.Filters[i]);
  }
  cfg.addToolbarElement("filter", "removeformat", 1);
}

Filter._pluginInfo =
{
  name          : "Filter",
  version       : "1.0",
  developer     : "Udo Schmal (gocher)",
  developer_url : "",
  sponsor       : "L.N.Schaffrath NeueMedien",
  sponsor_url   : "http://www.schaffrath-neuemedien.de/",
  c_owner       : "Udo Schmal & Schaffrath-NeueMedien",
  license       : "htmlArea"
};

Filter.prototype.add = function(filterName) {
  if(eval('typeof ' + filterName) == 'undefined') {
    var filter = Xinha.getPluginDir('Filter') + "/filters/" + filterName + ".js";
    var head = document.getElementsByTagName("head")[0];
    var evt = Xinha.is_ie ? "onreadystatechange" : "onload";
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = filter;
    script[evt] = function() {
      if(Xinha.is_ie && !/loaded|complete/.test(window.event.srcElement.readyState))  return;
    }
    head.appendChild(script);
    //document.write("<script type='text/javascript' src='" + plugin_file + "'></script>");
  }
};

Filter.prototype._lc = function(string) {
    return Xinha._lc(string, 'Filter');
};

Filter.prototype.buttonPress = function(editor) {
  var html = editor.getInnerHTML();
  for (var i = 0; i < editor.config.Filters.length; i++) {
    html = eval(editor.config.Filters[i])(html);
  }
  editor.setHTML(html);
};