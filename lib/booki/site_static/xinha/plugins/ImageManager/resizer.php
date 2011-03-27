<?php
header('Content-Type: text/javascript; charset=UTF-8');

/**
 * Resize images to a given size, and saving in a new file.
 * resize.php?img=/relative/path/to/image.jpg&width=<pixels>&height=<pixels>[&to=/relative/path/to/newimage.jpg]
 * relative to the base_dir given in config.inc.php
 * This is pretty much just thumbs.php with some mods, I'm too lazy to do it properly
 * @author $Author:ray $
 * @version $Id:resizer.php 922 2007-12-30 14:35:46Z ray $
 * @package ImageManager
 */

require_once('config.inc.php');
require_once('Classes/ImageManager.php');
require_once('Classes/Thumbnail.php');

function js_fail($message)    { echo 'alert(\'' . $message . '\'); false'; exit;   }
function js_success($resultFile)    { echo '\'' . $resultFile . '\''; exit;   }

//check for img parameter in the url
if(!isset($_GET['img']) || !isset($_GET['width']) || !isset($_GET['height']))
{
  js_fail('Missing parameter.');
}

$manager = new ImageManager($IMConfig);

//get the image and the full path to the image
$image = $_GET['img'];
$fullpath = Files::makeFile($manager->getImagesDir(),$image);

//not a file, so exit
if(!is_file($fullpath))
{
  js_fail("File {$fullpath} does not exist.");
}

$imgInfo = @getImageSize($fullpath);

//Not an image, bail out.
if(!is_array($imgInfo))
{
	js_fail("File {$fullpath} is not an image.");
}

if(!isset($_GET['to']))
{
  $resized    = $manager->getResizedName($fullpath,$_GET['width'],$_GET['height']);
  $_GET['to'] = $manager->getResizedName($image,$_GET['width'],$_GET['height'], FALSE);
}
else
{
  $resized = Files::makeFile($manager->getImagesDir(),$_GET['to']);
}

// Check to see if it already exists
if(is_file($resized))
{
	// And is newer
	if(filemtime($resized) >= filemtime($fullpath))
	{
		js_success($_GET['to']);
	}
}



// resize (thumbnailer will do this for us just fine)
$thumbnailer = new Thumbnail($_GET['width'],$_GET['height']);
$thumbnailer->proportional = FALSE;
$thumbnailer->createThumbnail($fullpath, $resized);

// did it work?
if(is_file($resized))
{
	js_success($_GET['to']);
}
else
{
	js_fail("Resize Failed.");
}
?>
