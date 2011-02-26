/*------------------------------------------*\
HtmlEntities for Xinha
____________________

Intended to faciliate the use of special characters with ISO 8 bit encodings.

Using the conversion map provided by mharrisonline in ticket #127

If you want to adjust the list, e.g. to except the characters that are available in the used charset,
edit Entities.js. 
You may save it under a different name using the xinha_config.HtmlEntities.EntitiesFile variable

ISO-8859-1 preset is default, set
  
  xinha_config.HtmlEntities.Encoding = null;

if you want all special characters to be converted or want to load a custom file 
\*------------------------------------------*/

function HtmlEntities(editor) {
	this.editor = editor;
}

HtmlEntities._pluginInfo = {
  name          : "HtmlEntities",
  version       : "1.0",
  developer     : "Raimund Meyer",
  developer_url : "http://x-webservice.net",
  c_owner       : "Xinha community",
  sponsor       : "",
  sponsor_url   : "",
  license       : "Creative Commons Attribution-ShareAlike License"
}
Xinha.Config.prototype.HtmlEntities =
{
	Encoding     : 'iso-8859-1',
	EntitiesFile : Xinha.getPluginDir("HtmlEntities") + "/Entities.js"
}
HtmlEntities.prototype.onGenerate = function() {
    var e = this.editor;
    var url = (e.config.HtmlEntities.Encoding) ?  Xinha.getPluginDir("HtmlEntities") + "/"+e.config.HtmlEntities.Encoding+".js" : e.config.HtmlEntities.EntitiesFile;
    var callback = function (getback) {
    	var specialReplacements = e.config.specialReplacements;
    	eval("var replacements =" + getback);
    	for (var i in  replacements)
		{
			specialReplacements[i] =  replacements[i];	
		}
    }
    Xinha._getback(url,callback);
}
