<?php
/**
 * ExtendedFileManager editorframe.php file.
 * Authors: Wei Zhuo, Afru, Krzysztof Kotowicz
 * Version: Updated on 08-01-2005 by Afru
 * Version: Updated on 21-06-2006 by Krzysztof Kotowicz
 * Version: Updated on 20-01-2008 by Raimund Meyer
 * Package: ExtendedFileManager (EFM 1.4)
 * http://www.afrusoft.com/htmlarea
 */
if(isset($_REQUEST['mode'])) $insertMode=$_REQUEST['mode'];
	if(!isset($insertMode)) $insertMode="image";

require_once('config.inc.php');
require_once('Classes/ExtendedFileManager.php');
require_once('../ImageManager/Classes/ImageEditor.php');

$manager = new ExtendedFileManager($IMConfig,$insertMode);
$editor = new ImageEditor($manager);
$imageInfo = $editor->processImage();

?>

<html>
<head>
	<title></title>
<link href="<?php print $IMConfig['base_url'];?>assets/editorFrame.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/wz_jsgraphics.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/EditorContent.js"></script>
<script type="text/javascript">
    var _backend_url = "<?php print $IMConfig['backend_url']."&mode=$insertMode"; ?>&";

    if(window.top)
    	Xinha = window.top.Xinha;

    function i18n(str) {
        return Xinha._lc(str, 'ImageManager');
    }

	var mode = "<?php echo $editor->getAction(); ?>" //crop, scale, measure
	var currentImageFile = "<?php if(count($imageInfo)>0) echo rawurlencode($imageInfo['file']); ?>";
	var fileSize = "<?php echo (round($imageInfo['filesize'] / 1024,1)).' KB' ?>";
	

<?php if ($editor->isFileSaved() == 1) { ?>
	alert(i18n('File saved.'));

    window.parent.opener.parent.refresh();
    window.parent.opener.selectImage
    (
  	'<?php echo $imageInfo['saveFile'] ?>',
  	'<?php echo $imageInfo['saveFile'] ?>'.replace(/^.*\/?([^\/]*)$/, '$1'),
  	<?php echo $imageInfo['width'] ?>,
  	<?php echo $imageInfo['height'] ?>
  	);
  	window.parent.close();
  	
<?php } else if ($editor->isFileSaved() == -1) { ?>
	alert(i18n('File was not saved.'));
<?php } ?>

</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/editorFrame.js"></script>
</head>

<body>
<div id="status"></div>
<div id="ant" class="selection" style="visibility:hidden"><img src="<?php print $IMConfig['base_url'];?>img/spacer.gif" width="0" height="0" border="0" alt="" id="cropContent"></div>
<?php if ($editor->isGDEditable() == -1) { ?>
	<div style="text-align:center; padding:10px;"><span class="error">GIF format is not supported, image editing not supported.</span></div>
<?php } ?>
<table height="100%" width="100%">
	<tr>
		<td>
<?php if(count($imageInfo) > 0 && is_file($imageInfo['fullpath'])) { ?>
	<span id="imgCanvas" class="crop"><img src="<?php echo $imageInfo['src']; ?>" <?php echo $imageInfo['dimensions']; ?> alt="" id="theImage" name="theImage"></span>
<?php } else { ?>
	<span class="error">No Image Available</span>
<?php } ?>
		</td>
	</tr>
</table>
</body>
</html>
