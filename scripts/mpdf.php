<?php

/* Parse the arguments */

$shortopts = "m:d:o:";
$longopts = array(
    "mpdf:",
    "dir:",
    "output:",
);

$options = getopt($shortopts, $longopts);

chdir($options["dir"]);

$file_input = $options["dir"]."/body.html";
$file_output = $options["output"];

/* Include mPDF library */
include($options["mpdf"]."/mpdf.php");


if(file_exists($options["dir"]."/config.json")) {
    $data = file_get_contents($options["dir"]."/config.json");
    $config = json_decode($data, true);
}

/* Read content */
$html_data = file_get_contents($file_input);

$html = '<tocpagebreak paging="on" links="on" toc-preHTML="&lt;h2&gt;Contents&lt;/h2&gt;" toc-bookmarkText="Content list" resetpagenum="1"  outdent="2em" pagenumstyle="1" toc-pagenumstyle="i" toc-suppress="0" suppress="0" toc-resetpagenum="1" />';

$html .= substr($html_data, 12, strlen($html_data)-27);

/* Create PDF */
$mpdf = new mPDF('utf-8');
$mpdf->mirrorMargins = 1;
$mpdf->AddPage('', '', '', '', 'on');

$mpdf->h2toc = array('H1'=>0, 'H2'=>0, 'H3'=>0, 'H4'=>0, 'H5'=>0, 'H6'=>0);
//$mpdf->SetDisplayMode('fullpage');


$mpdf->SetHTMLFooter('<div style="text-align: left;">{PAGENO}</div>', 'O');
$mpdf->SetHTMLFooter('<div style="text-align: right;">{PAGENO}</div>', 'E');

/* Add Styling */
if(file_exists($options["dir"]."/style.css")) {
    $data = file_get_contents($options["dir"]."/style.css");
    $mpdf->WriteHTML($data, 1);
}

/* Add Frontmatter */
if(file_exists($options["dir"]."/frontmatter.html")) {
    $data = file_get_contents($options["dir"]."/frontmatter.html");
    $mpdf->WriteHTML($data);
}

$mpdf->WriteHTML($html);

$mpdf->Output($file_output);

exit;
?>

