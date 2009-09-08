/*------------------------------------------*\
 GenericPlugin for Xinha
 _______________________
     
 Democase for plugin event handlers
\*------------------------------------------*/

GenericPlugin._pluginInfo = {
  name          : "GenericPlugin",
  version       : "1.0",
  developer     : "Xinha Developer Team",
  developer_url : "http://xinha.org",
  sponsor       : "",
  sponsor_url   : "",
  license       : "htmlArea"
}
function GenericPlugin(editor)
{
	this.editor = editor;
}

GenericPlugin.prototype.onGenerate = function ()
{

}
GenericPlugin.prototype.onGenerateOnce = function ()
{

}
GenericPlugin.prototype.inwardHtml = function(html)
{
	return html;
}
GenericPlugin.prototype.outwardHtml = function(html)
{
	return html;
}
GenericPlugin.prototype.onUpdateToolbar = function ()
{
	return false;
}

GenericPlugin.prototype.onExecCommand = function ( cmdID, UI, param )
{
	return false;
}

GenericPlugin.prototype.onKeyPress = function ( event )
{
	return false;
}

GenericPlugin.prototype.onMouseDown = function ( event )
{
	return false;
}

GenericPlugin.prototype.onBeforeSubmit = function ()
{
	return false;
}

GenericPlugin.prototype.onBeforeUnload = function ()
{
	return false;
}

GenericPlugin.prototype.onBeforeResize = function (width, height)
{
	return false;
}
GenericPlugin.prototype.onResize = function (width, height)
{
	return false;
}
/**
 * 
 * @param {String} action one of 'add', 'remove', 'hide', 'show', 'multi_hide', 'multi_show'
 * @param {DOMNode|Array} panel either the panel itself or an array like ['left','right','top','bottom']
 */
GenericPlugin.prototype.onPanelChange = function (action, panel)
{
	return false;
}
/**
 * 
 * @param {String} mode either 'textmode' or 'wysiwyg'
 */
GenericPlugin.prototype.onMode = function (mode)
{
	return false;
}
/**
 * 
 * @param {String} mode either 'textmode' or 'wysiwyg'
 */
GenericPlugin.prototype.onBeforeMode = function (mode)
{
	return false;
}
