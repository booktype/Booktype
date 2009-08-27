Word = function(html) {
    // Remove HTML comments
	html = html.replace(/<!--[\w\s\d@{}:.;,'"%!#_=&|?~()[*+\/\-\]]*-->/gi, "" );
	html = html.replace(/<!--[^\0]*-->/gi, '');
    // Remove all HTML tags
	html = html.replace(/<\/?\s*HTML[^>]*>/gi, "" );
    // Remove all BODY tags
    html = html.replace(/<\/?\s*BODY[^>]*>/gi, "" );
    // Remove all META tags
	html = html.replace(/<\/?\s*META[^>]*>/gi, "" );
    // Remove all SPAN tags
	html = html.replace(/<\/?\s*SPAN[^>]*>/gi, "" );
	// Remove all FONT tags
    html = html.replace(/<\/?\s*FONT[^>]*>/gi, "");
    // Remove all IFRAME tags.
    html = html.replace(/<\/?\s*IFRAME[^>]*>/gi, "");
    // Remove all STYLE tags & content
	html = html.replace(/<\/?\s*STYLE[^>]*>(.|[\n\r\t])*<\/\s*STYLE\s*>/gi, "" );
    // Remove all TITLE tags & content
	html = html.replace(/<\s*TITLE[^>]*>(.|[\n\r\t])*<\/\s*TITLE\s*>/gi, "" );
	// Remove javascript
    html = html.replace(/<\s*SCRIPT[^>]*>[^\0]*<\/\s*SCRIPT\s*>/gi, "");
    // Remove all HEAD tags & content
	html = html.replace(/<\s*HEAD[^>]*>(.|[\n\r\t])*<\/\s*HEAD\s*>/gi, "" );
	// Remove Class attributes
	html = html.replace(/<\s*(\w[^>]*) class=([^ |>]*)([^>]*)/gi, "<$1$3") ;
	// Remove Style attributes
	html = html.replace(/<\s*(\w[^>]*) style="([^"]*)"([^>]*)/gi, "<$1$3") ;
	// Remove Lang attributes
	html = html.replace(/<\s*(\w[^>]*) lang=([^ |>]*)([^>]*)/gi, "<$1$3") ;
	// Remove XML elements and declarations
	html = html.replace(/<\\?\?xml[^>]*>/gi, "") ;
	// Remove Tags with XML namespace declarations: <o:p></o:p>
	html = html.replace(/<\/?\w+:[^>]*>/gi, "") ;
	// Replace the &nbsp;
	html = html.replace(/&nbsp;/, " " );

	// Transform <p><br /></p> to <br>
	//html = html.replace(/<\s*p[^>]*>\s*<\s*br\s*\/>\s*<\/\s*p[^>]*>/gi, "<br>");
	html = html.replace(/<\s*p[^>]*><\s*br\s*\/?>\s*<\/\s*p[^>]*>/gi, "<br>");
	
	// Remove <P> 
	html = html.replace(/<\s*p[^>]*>/gi, "");
	
	// Replace </p> with <br>
	html = html.replace(/<\/\s*p[^>]*>/gi, "<br>");
	
	// Remove any <br> at the end
	html = html.replace(/(\s*<br>\s*)*$/, "");
	
	html = html.trim();
	return html;
};