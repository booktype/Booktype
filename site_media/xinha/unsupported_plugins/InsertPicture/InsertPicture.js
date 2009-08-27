// Insert Image plugin for Xinha
// Original Author - Udo Schmal
//
// (c) www.Schaffrath-NeueMedien.de  2004
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).

function InsertPicture(editor) {
  if ( typeof _editor_picturePath !== "string" )
    _editor_picturePath = Xinha.getPluginDir("InsertPicture") + "/demo_pictures/";
  InsertPicture.Scripting = "php"; //else "asp"
  editor.config.URIs.insert_image =  '../plugins/InsertPicture/InsertPicture.' + InsertPicture.Scripting + '?picturepath=' + _editor_picturePath;
}

InsertPicture._pluginInfo = {
  name          : "InsertPicture",
  version       : "1.0.2",
  developer     : "Udo Schmal",
  developer_url : "http://www.Schaffrath-NeueMedien.de/",
  sponsor       : "L.N.Schaffrath NeueMedien",
  sponsor_url   : "http://www.schaffrath-neuemedien.de/",
  c_owner       : "Udo Schmal",
  license       : "htmlArea"
};

