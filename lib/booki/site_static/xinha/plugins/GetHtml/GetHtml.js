/**
 Implemented now as GetHtmlImplementation plugin in modules/GetHtml/TransformInnerHTML.js
  */
  
function GetHtml(editor) {
    editor.config.getHtmlMethod = "TransformInnerHTML";
}

GetHtml._pluginInfo = {
	name          : "GetHtml",
	version       : "1.0",
	developer     : "Nelson Bright",
	developer_url : "http://www.brightworkweb.com/",
	sponsor       : "",
    sponsor_url   : "",
	license       : "htmlArea"
};
