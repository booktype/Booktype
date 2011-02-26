/*------------------------------------------*\
PreserveScripts for Xinha
____________________
Replace blocks of of PHP or JavaScript with icons in the editor, this way making it possible to edit sourcecode containing PHP, 
and preventing Javascript from being accidentally deleted because it's normally invisible

\*------------------------------------------*/

function PreserveScripts(editor) {
	this.editor = editor;
}

PreserveScripts._pluginInfo = {
  name          : "PreserveScripts",
  version       : "1.0",
  developer     : "Raimund Meyer",
  developer_url : "http://x-webservice.net",
  c_owner       : "Raimund Meyer",
  sponsor       : "",
  sponsor_url   : "",
  license       : "LGPL"
}
Xinha.Config.prototype.PreserveScripts =
{
	'preservePHP' : true,
	'preserveJS' : true
}
PreserveScripts.prototype.inwardHtml = function(html)
{
	var s = this;
	var c = s.editor.config.PreserveScripts;
	this.storage = {}; //empty the cache
	var i = 1;
	html = html.replace(/\n?<\?(php)?(\s|[^\s])*?\?>\n?/ig,
		function(m)
		{
			if ( c.preservePHP ) // if config set to false wipe out php completely, otherwise ugly fragments may remain
			{
				s.storage['PreserveScripts_'+i] = m;
				var r = '<img title="PHP" id="PreserveScripts_'+i+'" src="'+Xinha.getPluginDir("PreserveScripts")+'/php.png" />';
				i++;
				return r;
			}
			else
			{
				return '';
			}
		});
	if ( c.preserveJS )
	{
		html = html.replace(/\n?<script(\s|[^\s])*?<\/script>\n?/g,
			function(m)
			{
				s.storage['PreserveScripts_'+i] = m;
				var r = '<img title="JavaScript" id="PreserveScripts_'+i+'" src="' + Xinha.getPluginDir("PreserveScripts") + '/js.png" />';
				i++;
				return r;
			});	
	}
	return html;
}

PreserveScripts.prototype.outwardHtml = function(html)
{
	var s = this;
	html = html.replace(/<img[^>]*id="(PreserveScripts_\d+)"[^>]*>/g,function(m0,m1){return s.storage[m1];});
	return html;
}