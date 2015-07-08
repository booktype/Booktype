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
/*
$mpdf = new mPDF('', array($config["config"]["page_width_bleed"], $config["config"]["page_height_bleed"]), '', '',
  $config["config"]["settings"]["gutter"], $config["config"]["settings"]["side_margin"],
  $config["config"]["settings"]["top_margin"], $config["config"]["settings"]["bottom_margin"],
  $config["config"]["settings"]["header_margin"], $config["config"]["settings"]["footer_margin"]); */

$mpdf = new mPDF();

// Make it DOUBLE SIDED document
$mpdf->mirrorMargins = 1;

$mpdf->bleedMargin = $config["config"]["settings"]["bleed_size"];

// Add first page and suppress page counter
// When turned on, pages in ToC are not visible
//$mpdf->AddPage('', '', '', '' , '1');

$mpdf->h2toc = array(); 

/* Add Styling */
if(file_exists($options["dir"]."/style.css")) {
    $data = file_get_contents($options["dir"]."/style.css");
    $mpdf->WriteHTML($data, 1);
}


/* Add Frontmatter */
if(file_exists($options["dir"]."/frontmatter.html")) {
   $data = file_get_contents($options["dir"]."/frontmatter.html");
   $mpdf->WriteHTML($data, 2);
}


if(array_key_exists('show_footer', $config['config']['settings'])) {
    if(isset($config['config']['settings']['show_footer'])) {
//       $mpdf->SetHTMLFooter('<div style="text-align: left;">{PAGENO}</div>', 'E');
//       $mpdf->SetHTMLFooter('<div style="text-align: right;">{PAGENO}</div>', 'O');

      $mpdf->WriteHTML("<sethtmlpagefooter name=\"footer-left\" page=\"E\" value=\"on\" />
                        <sethtmlpagefooter name=\"footer-right\" page=\"O\" value=\"on\" />");
    }
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

