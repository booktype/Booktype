<?php
$snippets_file = 'snippets.html';

include_once('../../contrib/php-xinha.php');

if($passed_data = xinha_read_passed_data())
{
	extract($passed_data);      
}
$snippets = file_get_contents($snippets_file);
preg_match_all('/<!--(.*?)-->(.*?)<!--\/.*?-->/s',$snippets,$matches);
	
$array=array();
for ($i=0;$i<count($matches[1]);$i++)
{
	$id = $matches[1][$i];
	$html = $matches[2][$i];
	$array[] = array('id'=>$id,'HTML'=>$html);
}
print "var snippets = " . xinha_to_js($array);

?>