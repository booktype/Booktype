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
$html = substr($html_data, 12, strlen($html_data)-27);

/* Create PDF */
//$mpdf = new mPDF('', array($config["config"]["page_width"], $config["config"]["page_height"]));
$mpdf = new mPDF('');
//$mpdf->mirrorMargins = 1;
$mpdf->h2toc = array('H1'=>0, 'H2'=>0, 'H3'=>0, 'H4'=>0, 'H5'=>0, 'H6'=>0);

/* Add Styling */
if(file_exists($options["dir"]."/style.css")) {
    $data = file_get_contents($options["dir"]."/style.css");
    $mpdf->WriteHTML($data, 1);
}

if(array_key_exists('show_footer', $config['config']['settings'])) {
    if(isset($config['config']['settings']['show_footer'])) {
       $mpdf->SetHTMLFooter('<div style="text-align: left;">{PAGENO}</div>', 'O');
       $mpdf->SetHTMLFooter('<div style="text-align: right;">{PAGENO}</div>', 'E');
    }
}

/* Add Frontmatter */
if(file_exists($options["dir"]."/frontmatter.html")) {
   $data = file_get_contents($options["dir"]."/frontmatter.html");
   $mpdf->WriteHTML($data, 2);
}

$mpdf->WriteHTML($html, 2);

if(array_key_exists('title', $config['metadata'])) {
    if(isset($config['metadata']['title'])) {
        $mpdf->SetTitle($config['metadata']['title']);
    }
}

if(array_key_exists('creator', $config['metadata'])) {
    if(isset($config['metadata']['creator'])) {
        $mpdf->SetAuthor($config['metadata']['creator']);
    }
}

$mpdf->SetCreator('Booktype');

$mpdf->Output($file_output);

exit;
?>

