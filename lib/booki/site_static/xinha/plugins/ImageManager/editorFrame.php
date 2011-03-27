<?php 
/**
 * The frame that contains the image to be edited.
 * @author $Author:ray $
 * @version $Id:editorFrame.php 677 2007-01-19 22:24:36Z ray $
 * @package ImageManager
 */

require_once('config.inc.php');
require_once('Classes/ImageManager.php');
require_once('Classes/ImageEditor.php');

$manager = new ImageManager($IMConfig);
$editor = new ImageEditor($manager);
$imageInfo = $editor->processImage();

?>

<html>
<head>
	<title></title>
<script type="text/javascript">
_backend_url = "<?php print $IMConfig['backend_url']; ?>";
</script>

<link href="<?php print $IMConfig['base_url'];?>assets/editorFrame.css" rel="stylesheet" type="text/css" />	
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/wz_jsgraphics.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/EditorContent.js"></script>
<script type="text/javascript">

if(window.top)
	HTMLArea = window.top.HTMLArea;

function i18n(str) {
    return HTMLArea._lc(str, 'ImageManager');
}
	
	var mode = "<?php echo $editor->getAction(); ?>" //crop, scale, measure

var currentImageFile = "<?php if(count($imageInfo)>0) echo rawurlencode($imageInfo['file']); ?>";

<?php if ($editor->isFileSaved() == 1) { ?>
	alert(i18n('File saved.'));
  window.parent.opener.selectImage
    (
      '<?php echo $imageInfo['savedFile'] ?>',
      '<?php echo $imageInfo['savedFile'] ?>'.replace(/^.*\/?([^\/]*)$/, '$1'),
      <?php echo $imageInfo['width'] ?>,
      <?php echo $imageInfo['height'] ?>
    );
  window.parent.opener.parent.refresh();
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