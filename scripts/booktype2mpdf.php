<?php
error_reporting(0);

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
$html = file_get_contents($file_input);

/* Create PDF */

/*
$mpdf = new mPDF('', array($config["config"]["page_width_bleed"], $config["config"]["page_height_bleed"]), '', '',
  $config["config"]["settings"]["gutter"], $config["config"]["settings"]["side_margin"],
  $config["config"]["settings"]["top_margin"], $config["config"]["settings"]["bottom_margin"],
  $config["config"]["settings"]["header_margin"], $config["config"]["settings"]["footer_margin"]); 
*/

$mpdf = new mPDF();

// Specify whether to substitute missing characters in UTF-8 (multibyte) documents
$mpdf->useSubstitutions=false;

//Disables complex table borders etc. to improve performance
$mpdf->simpleTables = true; 

if(array_key_exists('mirror_margins', $config)) {
  if($config['mirror_margins']) {
    // Make it DOUBLE SIDED document
    $mpdf->mirrorMargins = 1;
  }
}

$mpdf->bleedMargin = $config["config"]["settings"]["bleed_size"];

$mpdf->h2toc = array(); 

/* Add Styling */
if(file_exists($options["dir"]."/style.css")) {
    $css_data = file_get_contents($options["dir"]."/style.css");
    $mpdf->WriteHTML($css_data, 1);
}

/* Add Frontmatter */
if(file_exists($options["dir"]."/frontmatter.html")) {
   $frontmatter_data = file_get_contents($options["dir"]."/frontmatter.html");
   $frontmatter_data = strtr($frontmatter_data, array('{TITLE}' => $config['metadata']['title']));

   $mpdf->WriteHTML($frontmatter_data, 2);
}

$mpdf->WriteHTML($html, 2);

/* Add Endmatter */
if(file_exists($options["dir"]."/endmatter.html")) {
   $data = file_get_contents($options["dir"]."/endmatter.html");
   $mpdf->WriteHTML($data, 2);
}

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
echo '{"status": 1, "pages": '.$mpdf->page.'}';
exit;
?>

