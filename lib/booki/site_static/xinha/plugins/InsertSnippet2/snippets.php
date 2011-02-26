<?php
/**
 * This is a reference implementation of how to get your snippets dynamically from a PHP data structure into InsertSnippet2's XML format.
 * <?php
 *   $categories = array('cat1','etc...'); //categories are optional
 *   $snippets = array(
 *     array('name'= 'snippet1','text'=>'some text'),
 *     array('name'= 'snippet2','text'=>'<p>some HTML</p>', 'varname'=>'{$var}','category'=>'cat1') //varname and category are optional
 *   )
 * 
 * ?>
 */
header("Content-type: text/xml");
print '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE snXML PUBLIC "Xinha InsertSnippet Data File" "http://x-webservice.net/res/snXML.dtd">';
?>
<snXML>
<categories>
<?php
foreach ((array)$categories as $c) {
	print '<c n="'.$c.'" />'."\n"; 
}

?>
</categories>
<snippets>
<?php
foreach ((array)$snippets as $s) {
	print '<s n="'.$s['name'].'" v="'.$s['varname'].'" c="'.$s['category'].'">
<![CDATA[
	'.$s['text'].'
]]>
</s>'."\n"; 
}
?>
</snippets>
</snXML>