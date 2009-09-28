<?php
/**
 * ExtendedFileManager images.php file. Shows folders and files.
 * Authors: Wei Zhuo, Afru, Krzysztof Kotowicz, Raimund Meyer
 * Version: Updated on 08-01-2005 by Afru
 * Version: Updated on 04-07-2006 by Krzysztof Kotowicz
 * Version: Updated on 29-10-2006 by Raimund Meyer
 * Version: Updated on 20-01-2008 by Raimund Meyer
 * Package: ExtendedFileManager (EFM 1.4)
 * http://www.afrusoft.com/htmlarea
 */

	if(isset($_REQUEST['mode'])) $insertMode=$_REQUEST['mode'];
	if(!isset($insertMode)) $insertMode="image";

require_once('config.inc.php');
require_once('Classes/ExtendedFileManager.php');
$backend_url_enc = htmlspecialchars( $IMConfig['backend_url'] );
//default path is /
$relative = '/';
$manager = new ExtendedFileManager($IMConfig, $insertMode);

//process any file uploads
$uploadStatus=$manager->processUploads();

//process any file renames
$renameStatus=$manager->processRenames();

//process paste
$pasteStatus = (isset($_GET['paste'])) ? 	$manager->processPaste() : false;

$refreshFile = ($manager->deleteFiles()) ? true : false;

$refreshDir = false;
//process any directory functions
if($manager->deleteDirs() || $manager->processNewDir() || $pasteStatus || $renameStatus )
	$refreshDir = true;


$diskInfo=$manager->getDiskInfo();

//check for any sub-directory request
//check that the requested sub-directory exists
//and valid
if(isset($_REQUEST['dir']))
{
	$path = rawurldecode($_REQUEST['dir']);
	if($manager->validRelativePath($path))
		$relative = $path;
}

$afruViewType = (isset($_REQUEST['viewtype'])) ? $afruViewType=$_REQUEST['viewtype'] : '';

if($afruViewType!="thumbview" && $afruViewType!="listview")
{
  $afruViewType=$IMConfig['view_type'];
}
//get the list of files and directories
$list = $manager->getFiles($relative);


/* ================= OUTPUT/DRAW FUNCTIONS ======================= */


/**
 * Draw folders and files. Changed by Afru
 */
function drawDirs_Files($list, &$manager) 
{
	global $relative, $afruViewType, $IMConfig, $insertMode,$backend_url_enc;

    switch ($afruViewType) {
        case 'listview':
    		$maxNameLength = 30;
    		?>
            <table class="listview" id="listview">
            <thead>
            <tr><th>Name</th><th>Size</th><th>Image Size</th><th>Date Modified</th><th>&nbsp;</th></tr></thead>
            <tbody>
            <?php
    		// start of foreach for draw listview folders .
    		foreach($list[0] as $path => $dir)
    		{ ?>
    			<tr>
    			<td><span style="width:20px;"><img src="<?php print $IMConfig['base_url'];?>icons/folder_small.gif" alt="" /></span>
				<a href="<?php print $backend_url_enc; ?>__function=images&amp;mode=<?php echo $insertMode;?>&amp;dir=<?php echo rawurlencode($path); ?>&amp;viewtype=<?php echo $afruViewType; ?>" onclick="updateDir('<?php echo $path; ?>')" title="<?php echo $dir['entry']; ?>">
    			<?php
    			if(strlen($dir['entry'])>$maxNameLength) echo substr($dir['entry'],0,$maxNameLength)."..."; else echo $dir['entry'];
    			?>
    			</a></td>
    			<td colspan="2" >Folder</td>

    			<td ><?php echo date($IMConfig['date_format'],$dir['stat']['mtime']); ?></td>

    			<td class="actions" >
    				<a href="<?php print $backend_url_enc; ?>__function=images&amp;mode=<?php echo $insertMode;?>&amp;dir=<?php echo $relative; ?>&amp;deld=<?php echo rawurlencode($path); ?>&amp;viewtype=<?php echo $afruViewType; ?>" title="Trash" onclick="return confirmDeleteDir('<?php echo $dir['entry']; ?>', <?php echo $dir['count']; ?>);" style="border:0px;"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash" border="0" /></a>
			    	<?php if ($IMConfig['allow_rename']) { ?>
			                    <a href="#" title="Rename" onclick="renameDir('<?php echo rawurlencode($dir['entry']);?>'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_rename.gif" height="15" width="15" alt="Rename" border="0" /></a>
			        <?php }  ?>
    				<?php if ($IMConfig['allow_cut_copy_paste']) { ?>
                    <a href="#" title="Cut" onclick="copyDir('<?php echo rawurlencode($dir['entry']);?>','move'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_cut.gif" height="15" width="15" alt="Cut" /></a>
                     <a href="#" title="Copy" onclick="copyDir('<?php echo rawurlencode($dir['entry']);?>','copy'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_copy.gif" height="15" width="15" alt="Copy" /></a>
     		   		<?php }  ?>
    			</td>
    			</tr>
    		  <?php
    		} // end of foreach for draw listview folders .

    		clearstatcache();

    		// start of foreach for draw listview files .
    		foreach($list[1] as $entry => $file)
    		{
    			?>
                <tr>
        		  <td><span style="width:20px;"><img src="<?php print $IMConfig['base_url']; if(is_file('icons/'.$file['ext'].'_small.gif')) echo "icons/".$file['ext']."_small.gif"; else echo $IMConfig['default_listicon']; ?>" alt="" /></span>
					<a href="#" class="thumb" style="cursor: pointer;" ondblclick="this.onclick();window.top.onOK();" onclick="selectImage('<?php echo $file['relative'];?>', '<?php echo preg_replace('#\..{3,4}$#', '', $entry); ?>', <?php echo $file['image'][0];?>, <?php echo $file['image'][1]; ?>);return false;" title="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>" <?php if ($insertMode == 'image') { ?> onmouseover="showPreview('<?php echo $file['relative'];?>')" onmouseout="showPreview(window.parent.document.getElementById('f_url').value)" <?php } ?> >
        			<?php
        			if(strlen($entry)>$maxNameLength) echo substr($entry,0,$maxNameLength)."..."; else echo $entry;
        			?>
                  </a></td>
                  <td><?php echo Files::formatSize($file['stat']['size']); ?></td>
                  <td><?php if($file['image'][0] > 0){ echo $file['image'][0].'x'.$file['image'][1]; } ?></td>
    			  <td ><?php echo date($IMConfig['date_format'],$file['stat']['mtime']); ?></td>
                  <td class="actions">
                    <?php if($IMConfig['img_library'] && $IMConfig['allow_edit_image'] && $file['image'][0] > 0) { ?>
                    <a href="javascript:;" title="Edit" onclick="editImage('<?php echo rawurlencode($file['relative']);?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_pencil.gif" height="15" width="15" alt="Edit" border="0" /></a>
                    <?php }  ?>  
                    <a href="<?php print $backend_url_enc; ?>__function=images&amp;dir=<?php echo $relative; ?>&amp;delf=<?php echo rawurlencode($file['relative']);?>&amp;mode=<?php echo $insertMode;?>&amp;viewtype=<?php echo $afruViewType; ?>" title="Trash" onclick="return confirmDeleteFile('<?php echo $entry; ?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash" border="0" /></a>
        			<?php if ($IMConfig['allow_rename']) { ?>
                    <a href="#" title="Rename" onclick="renameFile('<?php echo rawurlencode($file['relative']);?>'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_rename.gif" height="15" width="15" alt="Rename" border="0" /></a>
                    <?php }  ?>
        			<?php if ($IMConfig['allow_cut_copy_paste']) { ?>
                    <a href="#" title="Cut" onclick="copyFile('<?php echo rawurlencode($entry);?>','move'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_cut.gif" height="15" width="15" alt="Cut" /></a>
                     <a href="#" title="Copy" onclick="copyFile('<?php echo rawurlencode($entry);?>','copy'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_copy.gif" height="15" width="15" alt="Copy" /></a>
                    <?php }  ?>
                  </td>
                </tr>
    		  <?php
    		}//end of foreach of draw listview files
            ?>
            </tbody>
            </table>
            <?php
        break;
        case 'thumbview': // thumbview is default
        default:
    		$maxFileNameLength=16;
    		$maxFolderNameLength=16;
    		// start of foreach for draw thumbview folders.
    		foreach($list[0] as $path => $dir)
    		{ ?>
    <div class="dir_holder">
      <a class="dir" href="<?php print $backend_url_enc;?>__function=images&amp;mode=<?php echo $insertMode;?>&amp;dir=<?php echo rawurlencode($path); ?>&amp;viewtype=<?php echo $afruViewType; ?>" onclick="updateDir('<?php echo $path; ?>')" title="<?php echo $dir['entry']; ?>"><img src="<?php print $IMConfig['base_url'];?>img/folder.gif" height="80" width="80" alt="<?php echo $dir['entry']; ?>" /></a>

      <div class="fileName">
      <?php if(strlen($dir['entry']) > $maxFolderNameLength)
                echo substr($dir['entry'], 0, $maxFolderNameLength) . "...";
              else
                echo $dir['entry']; ?>
      </div>
      <div class="edit">
        <a href="<?php print $backend_url_enc;?>__function=images&amp;mode=<?php echo $insertMode;?>&amp;dir=<?php echo $relative; ?>&amp;deld=<?php echo rawurlencode($path); ?>&amp;viewtype=<?php echo $afruViewType; ?>" title="Trash" onclick="return confirmDeleteDir('<?php echo $dir['entry']; ?>', <?php echo $dir['count']; ?>);"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash" /></a>
    	<?php if ($IMConfig['allow_rename']) { ?>
                    <a href="#" title="Rename" onclick="renameDir('<?php echo rawurlencode($dir['entry']);?>'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_rename.gif" height="15" width="15" alt="Rename" border="0" /></a>
        <?php }  ?>
        <?php if ($IMConfig['allow_cut_copy_paste']) { ?>
                    <a href="#" title="Cut" onclick="copyDir('<?php echo rawurlencode($dir['entry']);?>','move'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_cut.gif" height="15" width="15" alt="Cut" /></a>
                     <a href="#" title="Copy" onclick="copyDir('<?php echo rawurlencode($dir['entry']);?>','copy'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_copy.gif" height="15" width="15" alt="Copy" /></a>
        <?php }  ?>
      </div>
    </div>
    		  <?php
    		} // end of foreach for draw thumbview folders.


    		// start of foreach for draw thumbview files.
    		foreach($list[1] as $entry => $file)
    		{
    			$afruimgdimensions=$manager->checkImageSize($file['relative']);
    			$thisFileNameLength = $maxFileNameLength;
    			?>
                <div class="thumb_holder" id="holder_<?php echo asc2hex($entry) ?>">
                  <a href="#" class="thumb" style="cursor: pointer;" ondblclick="this.onclick();window.top.onOK();" onclick="selectImage('<?php echo $file['relative'];?>', '<?php echo preg_replace('#\..{3,4}$#', '', $entry); ?>', <?php echo $file['image'][0];?>, <?php echo $file['image'][1]; ?>);return false;" title="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>">
                    <img src="<?php print $manager->getThumbnail($file['relative']); ?>" alt="<?php echo $entry; ?> - <?php echo Files::formatSize($file['stat']['size']); ?>" />
                  </a>
                   <div class="fileName">
                   <?php
            			if(strlen($entry) > $thisFileNameLength + 3) echo strtolower(substr($entry,0,$thisFileNameLength))."..."; else echo $entry;
            		?>
                   </div>
                  <div class="edit">
                    <?php if($IMConfig['img_library'] && $IMConfig['allow_edit_image'] && $file['image'][0] > 0 )
                    { ?>
                    <a href="javascript:;" title="Edit" onclick="editImage('<?php echo rawurlencode($file['relative']);?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_pencil.gif" height="15" width="15" alt="Edit" /></a>
            		<?php $thisFileNameLength -= 3; } ?>
                    <a href="<?php print $backend_url_enc; ?>__function=images&amp;mode=<?php echo $insertMode;?>&amp;dir=<?php echo $relative; ?>&amp;delf=<?php echo rawurlencode($file['relative']);?>&amp;viewtype=<?php echo $afruViewType; ?>" title="Trash" onclick="return confirmDeleteFile('<?php echo $entry; ?>');"><img src="<?php print $IMConfig['base_url'];?>img/edit_trash.gif" height="15" width="15" alt="Trash" /></a>
        			<?php if ($IMConfig['allow_rename']) { ?>
                    <a href="#" title="Rename" onclick="renameFile('<?php echo rawurlencode($file['relative']);?>'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_rename.gif" height="15" width="15" alt="Rename" /></a>
                    <?php $thisFileNameLength -= 3; }  ?>
                	<?php if ($IMConfig['allow_cut_copy_paste']) { ?>
                    <a href="#" title="Cut" onclick="copyFile('<?php echo rawurlencode($entry);?>','move'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_cut.gif" height="15" width="15" alt="Cut" /></a>
                     <a href="#" title="Copy" onclick="copyFile('<?php echo rawurlencode($entry);?>','copy'); return false;"><img src="<?php print $IMConfig['base_url'];?>img/edit_copy.gif" height="15" width="15" alt="Copy" /></a>
                    <?php $thisFileNameLength -= 6; }  ?>
            		
                  </div>
                </div>
    		  <?php
    		}//end of foreach of draw thumbview files

    }
}//end of function drawDirs_Files


/**
 * No directories and no files.
 */
function drawNoResults() 
{
?>
<div class="noResult">No Files Found</div>
<?php
}

/**
 * No directories and no files.
 */
function drawErrorBase(&$manager) 
{
?>
<div class="error"><span>Invalid base directory:</span> <?php echo $manager->getImagesDir(); ?></div>
<?php
}

/**
 * Utility to convert ascii string to hex
 */
function asc2hex ($temp)
{
  $data = '';
  $len = strlen($temp);
  for ($i=0; $i<$len; $i++) $data.=sprintf("%02x",ord(substr($temp,$i,1)));
  return $data;
}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>File List</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<link href="<?php print $IMConfig['base_url'];?>assets/imagelist.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/dialog.js"></script>
<script type="text/javascript">
/*<![CDATA[*/

    var _backend_url = "<?php print $IMConfig['backend_url']; ?>";

	if(window.top)
		Xinha = window.top.Xinha;

	function hideMessage()
	{
		var topDoc = window.top.document;
		var messages = topDoc.getElementById('messages');
		if (messages)
		{
			messages.style.display = "none";
		}
		//window.parent.resize();
	}

	init = function()
	{
        __dlg_translate('ExtendedFileManager');
        
		hideMessage();
		<?php if ($afruViewType == 'listview')
			print "var d = new dragTableCols('listview');";
		
		if(isset($uploadStatus) && !is_numeric($uploadStatus) && !is_bool($uploadStatus))
		echo "alert(i18n('$uploadStatus'));";
		else if(isset($uploadStatus) && $uploadStatus==false)
		echo 'alert(i18n("Unable to upload File. \nEither Maximum file size [$max_size='.($insertMode == 'image' ? $IMConfig['max_filesize_kb_image'] : $IMConfig['max_filesize_kb_link'] ).'$ KB] exceeded or\nFolder doesn\'t have write permission."));';
		?>

		<?php
		if(isset($renameStatus) && !is_numeric($renameStatus) && !is_bool($renameStatus))
		echo 'alert(i18n("'.$renameStatus.'"));';
		else if(isset($renameStatus) && $renameStatus===false)
		echo 'alert(i18n("Unable to rename file. File of the same name already exists or\nfolder doesn\'t have write permission."));';
		?>
		
		<?php
		if (isset($pasteStatus) && is_numeric($pasteStatus))
		{
			switch ($pasteStatus)
			{
				case 100 :
					$pasteStatus = 'Source file/folder not found.';
				break;
				case 101 :
					$pasteStatus = 'Copy failed.\nMaybe folder doesn\'t have write permission.';
				break;
				case 102 :
					$pasteStatus = 'Could not create destination folder.';
				break;
				case 103 :
					$pasteStatus = 'File pasted OK.';
				break;
				case 104 :
					$pasteStatus = 'Destination file/folder already exists.';
				break;
			}
		}
		if(isset($pasteStatus) && !is_bool($pasteStatus))
		{
			echo 'alert(i18n("'.$pasteStatus.'"));';
		}
		?>

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
	}
    
	function editImage(image) 
	{
		var url = "<?php print $IMConfig['backend_url']; ?>__function=editor&img="+image+"&mode=<?php print $insertMode ?>";
        Dialog(url, function(param)
		{
			if (!param) { // user must have pressed Cancel
				return false;
			} else
			{
				return true;
			}
		}, null);
	}

/*]]>*/
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/images.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/popup.js"></script>
<script type="text/javascript">
<!--
// Koto: why emptying? commented out
//if(window.top.document.getElementById('manager_mode').value=="image")
//emptyProperties();
<?php if(isset($diskInfo)) echo 'updateDiskMesg(i18n(\''.$diskInfo.'\'));'; ?>
//-->
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/dragTableCols.js"></script>
</head>

<body>
<?php if ($manager->isValidBase() == false) { drawErrorBase($manager); }
	elseif(count($list[0]) > 0 || count($list[1]) > 0) { ?>
	<?php drawDirs_Files($list, $manager); ?>
<?php } else { drawNoResults(); } ?>
</body>
</html>
