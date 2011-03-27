// Spell Checker Plugin for HTMLArea-3.0
// Sponsored by www.americanbible.org
// Implementation by Mihai Bazon, http://dynarch.com/mishoo/
//
// (c) dynarch.com 2003.
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).
//
// $Id:spell-checker.js 856M 2007-06-13 18:34:34Z (local) $

Xinha.Config.prototype.SpellChecker = { 'backend': 'php', 'personalFilesDir' : '', 'defaultDictionary' : 'en_GB', 'utf8_to_entities' : true };

function SpellChecker(editor) {
  this.editor = editor;

  var cfg = editor.config;
  var bl = SpellChecker.btnList;
  var self = this;

  // see if we can find the mode switch button, insert this before that
  var id = "SC-spell-check";
  cfg.registerButton(id, this._lc("Spell-check"), editor.imgURL("spell-check.gif", "SpellChecker"), false,
             function(editor, id) {
               // dispatch button press event
               self.buttonPress(editor, id);
             });

  cfg.addToolbarElement("SC-spell-check", "htmlmode", 1);
}

SpellChecker._pluginInfo = {
  name          : "SpellChecker",
  version       : "1.0",
  developer     : "Mihai Bazon",
  developer_url : "http://dynarch.com/mishoo/",
  c_owner       : "Mihai Bazon",
  sponsor       : "American Bible Society",
  sponsor_url   : "http://www.americanbible.org",
  license       : "htmlArea"
};

SpellChecker.prototype._lc = function(string) {
    return Xinha._lc(string, 'SpellChecker');
};

SpellChecker.btnList = [
  null, // separator
  ["spell-check"]
  ];

SpellChecker.prototype.buttonPress = function(editor, id) {
  switch (id) {
      case "SC-spell-check":
    SpellChecker.editor = editor;
    SpellChecker.init = true;
    var uiurl = Xinha.getPluginDir("SpellChecker") + "/spell-check-ui.html";
    var win;
    if (Xinha.is_ie) {
      win = window.open(uiurl, "SC_spell_checker",
            "toolbar=no,location=no,directories=no,status=no,menubar=no," +
            "scrollbars=no,resizable=yes,width=600,height=450");
    } else {
      win = window.open(uiurl, "SC_spell_checker",
            "toolbar=no,menubar=no,personalbar=no,width=600,height=450," +
            "scrollbars=no,resizable=yes");
    }
    win.focus();
    break;
  }
};

// this needs to be global, it's accessed from spell-check-ui.html
SpellChecker.editor = null;