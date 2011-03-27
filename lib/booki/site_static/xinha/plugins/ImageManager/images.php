<?php 
/**
 * Show a list of images in a long horizontal table.
 * @author $Author:ray $
 * @version $Id:images.php 987 2008-04-12 12:39:04Z ray $
 * @package ImageManager
 */

require_once('config.inc.php');
require_once('ddt.php');
require_once('Classes/ImageManager.php');

// uncomment for debugging

// _ddtOn();

//default path is /
$relative = '/';
$manager = new ImageManager($IMConfig);

//process any file uploads
$manager->processUploads();

$manager->deleteFiles();

$refreshDir = false;
//process any directory functions
if($manager->deleteDirs() || $manager->processNewDir())
	$refreshDir = true;

//check for any sub-directory request
//check that the requested sub-directory exists
//and valid
if(isset($_REQUEST['dir']))
{
	$path = rawurldecode($_REQUEST['dir']);
	if($manager->validRelativePath($path))
		$relative = $path;
}


$manager = new ImageManager($IMConfig);


//get the list of files and directories
$list = $manager->getFiles($relative);


/* ================= OUTPUT/DRAW FUNCTIONS ======================= */

/**
 * Draw the files in an table.
 */
function drawFiles($list, &$manager)
{
	global $relative;
	global $IMConfig;

    switch($IMConfig['ViewMode'])
    {
      case 'details':
      {
        ?>
        <script language="Javascript">
          <!--
            function showPreview(f_url)
            {
              
              window.parent.document.getElementById('f_preview').src = 
                window.parent._backend_url + '__function=thumbs&img=' + f_url;
            }
          //-->
        </script>
        <table class="listview">
        <thead>
        <tr><th>Name</th><th>Filesize</th><th>Dimensions</th></tr></thead>
        <tbody>
          <?php
          foreach($list as $entry => $file)
          {
            ?>
            <tr>
              <th><a href="#" class="thumb" style="cursor: pointer;" onclick="selectImage('<?php echo $file['relative'];?>', '<?php echo $entry; ?>', <?php echo $file['image'][0];?>, <?php echo $file['image'][1]; ?>);return false;" title="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>" onmouseover="showPreview('<?php echo $file['relative'];?>')" onmouseout="showPreview(window.parent.document.getElementById('f_url').value)" ><?php echo $entry ?></a></th>
              <td><?php echo Files::formatSize($file['stat']['size']); ?></td>
              <td><?php if($file['image']){ echo $file['image'][0].'x'.$file['image'][1]; } ?></td>
              <td class="actions">
                <a href="<?php print $IMConfig['backend_url']; ?>__function=images&dir=<?php echo $relative; ?>&amp;delf=<?php echo rawurlencode($file['relative']);?>" title="Trash" onclick="return confirmDeleteFile('<?php echo $entry; ?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash" border="0"  /></a>
        
                <a href="javascript:;" title="Edit" onclick="editImage('<?php echo rawurlencode($file['relative']);?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_pencil.gif" height="15" width="15" alt="Edit" border="0" /></a>
              </td>
            </tr>
            <?php        
          }
          ?>
        </tbody>
        </table>
        <?php
      }      
      break;
      
      case 'thumbs':
      default      :
      {
	foreach($list as $entry => $file)
	{
		?>
    <div class="thumb_holder" id="holder_<?php echo asc2hex($entry) ?>">
      <a href="#" class="thumb" style="cursor: pointer;" onclick="selectImage('<?php echo $file['relative'];?>', '<?php echo $entry; ?>', <?php echo $file['image'][0];?>, <?php echo $file['image'][1]; ?>);return false;" title="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>">
        <img src="<?php print $manager->getThumbnail($file['relative']); ?>" alt="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>"/>
      </a>
      <div class="edit">
        <a href="<?php print $IMConfig['backend_url']; ?>__function=images&dir=<?php echo $relative; ?>&amp;delf=<?php echo rawurlencode($file['relative']);?>" title="Trash" onclick="return confirmDeleteFile('<?php echo $entry; ?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash"  /></a>

        <a href="javascript:;" title="Edit" onclick="editImage('<?php echo rawurlencode($file['relative']);?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_pencil.gif" height="15" width="15" alt="Edit" /></a>

        <?php if($file['image']){ echo $file['image'][0].'x'.$file['image'][1]; } else echo $entry;?>
      </div>
    </div>
	  <?php
        }
      }
    }	
}//function drawFiles


/**
 * Draw the directory.
 */
function drawDirs($list, &$manager) 
{
	global $relative;
   global $IMConfig;

  switch($IMConfig['ViewMode'])
  {
    case 'details':
    {
        
    }
    break; 
    
    case 'thumbs':
    default      :
    {
	foreach($list as $path => $dir) 
	{ ?>
    <div class="dir_holder">
      <a class="dir" href="<?php print $IMConfig['backend_url'];?>__function=images&dir=<?php echo rawurlencode($path); ?>" onclick="updateDir('<?php echo $path; ?>')" title="<?php echo $dir['entry']; ?>"><img src="<?php print $IMConfig['base_url'];?>img/folder.gif" height="80" width="80" alt="<?php echo $dir['entry']; ?>" /></a>

      <div class="edit">
        <a href="<?php print $IMConfig['backend_url'];?>__function=images&dir=<?php echo $relative; ?>&amp;deld=<?php echo rawurlencode($path); ?>" title="Trash" onclick="return confirmDeleteDir('<?php echo $dir['entry']; ?>', <?php echo $dir['count']; ?>);"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash"/></a>
        <?php echo $dir['entry']; ?>
      </div>
    </div>
	  <?php 
	} //foreach
    }
  }
  
	
}//function drawDirs


/**
 * No directories and no files.
 */
function drawNoResults() 
{
?>
<div class="noResult">No Images Found</div>
<?php 
}

/**
 * No directories and no files.
 */
function drawErrorBase(&$manager) 
{
?>
<div class="error"><span>Invalid base directory:</span> <?php echo $manager->config['images_dir']; ?></div>
<?php 
}

/**
 * Utility to convert ascii string to hex
 */
function asc2hex ($temp)
{
  $len = strlen($temp);
  $data = "";
  for ($i=0; $i<$len; $i++) $data.=sprintf("%02x",ord(substr($temp,$i,1)));
  return $data;
}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
<head>
	<title>Image List</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<link href="<?php print $IMConfig['base_url'];?>assets/imagelist.css" rel="stylesheet" type="text/css" />
<script type="text/javascript">
_backend_url = "<?php print $IMConfig['backend_url']; ?>";
</script>

<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/dialog.js"></script>
<script type="text/javascript">
/*<![CDATA[*/

	if(window.top)
    HTMLArea = Xinha    = window.top.Xinha;

	function hideMessage()
	{
		var topDoc = window.top.document;
		var messages = topDoc.getElementById('messages');
		if(messages)
			messages.style.display = "none";
	}

	init = function()
	{
	  __dlg_translate('ImageManager');
		hideMessage();
		var topDoc = window.top.document;

<?php 
	//we need to refesh the drop directory list
	//save the current dir, delete all select options
	//add the new list, re-select the saved dir.
	if($refreshDir) 
	{ 
		$dirs = $manager->getDirs();
?>
		var selection = topDoc.getElementById('dirPath');
		var currentDir = selection.options[selection.selectedIndex].text;

		while(selection.length > 0)
		{	selection.remove(0); }
		
		selection.options[selection.length] = new Option("/","<?php echo rawurlencode('/'); ?>");	
		<?php foreach($dirs as $relative=>$fullpath) { ?>
		selection.options[selection.length] = new Option("<?php echo $relative; ?>","<?php echo rawurlencode($relative); ?>");		
		<?php } ?>
		
		for(var i = 0; i < selection.length; i++)
		{
			var thisDir = selection.options[i].text;
			if(thisDir == currentDir)
			{
				selection.selectedIndex = i;
				break;
			}
		}		
<?php } ?>
    update_selected();
	}	

	function editImage(image) 
	{
		var url = "<?php print $IMConfig['backend_url']; ?>__function=editor&img="+image;
		Dialog(url, function(param) 
		{
			if (!param) // user must have pressed Cancel
				return false;
			else
			{
				return true;
			}
		}, null);		
	}

/*]]>*/
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/images.js"></script>
<script type="text/javascript" src="../../popups/popup.js"></script>
<script type="text/javascript" src="assets/popup.js"></script>
</head>

<body>
<?php if ($manager->isValidBase() == false) { drawErrorBase($manager); } 
	elseif(count($list[0]) > 0 || count($list[1]) > 0) { ?>

	<?php drawDirs($list[0], $manager); ?>
	<?php drawFiles($list[1], $manager); ?>

<?php } else { drawNoResults(); } ?>
</body>
</html>
