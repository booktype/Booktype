<?php
/**
 * The main GUI for the ExtendedFileManager.
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
	
	$manager = new ExtendedFileManager($IMConfig);
	$dirs = $manager->getDirs();

	// calculate number of table rows to span for the preview cell
	$num_rows = 4; // filename & upload & disk info message & width+margin
		
	if ($insertMode=='image')
	{
		if ($IMConfig['images_enable_styling'] === false)
		{
			$hidden_fields[] = 'f_margin';
			$hidden_fields[] = 'f_padding';
			$hidden_fields[] = 'f_border';
			$hidden_fields[] = 'f_backgroundColor';
			$hidden_fields[] = 'f_borderColor';
			$num_rows +=2;
		}
		else if ($IMConfig['use_color_pickers'] === false)
		{
			$hidden_fields[] = 'f_backgroundColor';
			$hidden_fields[] = 'f_borderColor';
			$num_rows +=2;
		}
		
		if ($IMConfig['images_enable_align'] === false)
		{
			$hidden_fields[] = 'f_align';
		}
		if ($IMConfig['images_enable_alt'])
		{
			$num_rows++;
		}
		else 
		{
			$hidden_fields[] = 'f_alt';
		}
		if ($IMConfig['images_enable_title'])
		{
			$num_rows++;
		}
		else 
		{
			$hidden_fields[] = 'f_title';
		}
	}
	
	if ($insertMode == 'link')
	{
		if ($IMConfig['link_enable_target'] === false)
		{
			$hidden_fields[] = 'f_target';
		}
		$num_rows +=2;
	}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>Insert <?php echo ($insertMode == 'image' ? 'Image' : 'File Link') ?></title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
 <link href="<?php print $IMConfig['base_url'];?>assets/manager.css" rel="stylesheet" type="text/css" />
 <link href="../../popups/popup.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="../../popups/popup.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/popup.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/dialog.js"></script>
<?php if (!empty($IMConfig['use_color_pickers'])) { ?><script type="text/javascript" src="../../modules/ColorPicker/ColorPicker.js"></script><?php } ?>
<script type="text/javascript">
/* <![CDATA[ */

	if(window.opener)
		Xinha = window.opener.Xinha;
		
	var thumbdir = "<?php echo $IMConfig['thumbnail_dir']; ?>";
	var base_url = "<?php echo $manager->getImagesURL(); ?>";
    var _backend_url = "<?php print $IMConfig['backend_url']; ?>";
    var _resized_prefix = "<?php echo $IMConfig['resized_prefix']; ?>";
  	var _resized_dir = "<?php echo $IMConfig['resized_dir']; ?>";
    var manager_show_target = <?php echo ($insertMode == 'link' && $IMConfig['link_enable_target'] ? 'true'  : 'false') ?>;

	<?php
	if(isset($_REQUEST['mode']))
	{
		echo 'var manager_mode="'.$_REQUEST['mode'].'";';
	}
	else
	{
		echo 'var manager_mode="image";';
	}
	//IE doesn't like a relative URL when changing a window's location
	$iframe_url = str_replace( array("backend.php","manager.php"), "", $_SERVER["PHP_SELF"] ) . $IMConfig['backend_url'];
	?>
	
	var iframeUrl = '<?php print $iframe_url ?>__function=images&mode=<?php echo $insertMode;?>&viewtype=<?php echo $IMConfig['view_type'] ?>';

/* ]]> */
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/manager.js"></script>
</head>
<body class="dialog" >
<div class="title">Insert <?php echo ($insertMode == 'image' ? 'Image' : 'File Link') ?></div>
<form action="<?php print htmlspecialchars($IMConfig['backend_url']); ?>" id="uploadForm" method="post" enctype="multipart/form-data">
<input type="hidden" name="__plugin" value="ExtendedFileManager" />
<input type="hidden" name="__function" value="images" />
<input type="hidden" name="mode" value="<?php echo $insertMode; ?>" />
<input type="hidden" id="manager_mode" value="<?php echo $insertMode;?>" />
<fieldset><legend>File Manager</legend>
<table border="0" cellpadding="0" cellspacing="0" width="100%">
<tr>
<td nowrap="nowrap" style="padding:10px;">

	<label for="dirPath">Directory</label>
	<select name="dir" class="dirWidth" id="dirPath" onchange="updateDir(this)">
	<option value="/">/</option>
<?php foreach($dirs as $relative=>$fullpath) { ?>
		<option value="<?php echo rawurlencode($relative); ?>"><?php echo $relative; ?></option>
<?php } ?>
	</select>

	<a href="#" onclick="javascript: goUpDir();" title="Directory Up"><img src="<?php print $IMConfig['base_url'];?>img/btnFolderUp.gif" height="15" width="15" alt="Directory Up" /></a>


<?php if($IMConfig['safe_mode'] == false && $IMConfig['allow_new_dir']) { ?>
	<a href="#" onclick="newFolder();" title="New Folder"><img src="<?php print $IMConfig['base_url'];?>img/btnFolderNew.gif" height="15" width="15" alt="New Folder" /></a>
<?php } ?>
<span id="pasteBtn"></span>

	<select name="viewtype" id="viewtype" onchange="updateView()">
	<option value="thumbview" <?php if($IMConfig['view_type']=="thumbview") echo 'selected="selected"';?> >Thumbnail View</option>
	<option value="listview" <?php if($IMConfig['view_type']=="listview") echo 'selected="selected"';?> >List View</option>
	</select>
</td>
</tr>
<tr><td style="padding:10px; padding-top:0px;">
	<div id="messages"><span id="message">Loading</span><img src="<?php print $IMConfig['base_url'];?>img/dots.gif" width="22" height="12" alt="..." /></div>
	<iframe src="about:blank" name="imgManager" id="imgManager" class="imageFrame" scrolling="auto" title="Image Selection" frameborder="0"></iframe>
</td></tr>
</table>
</fieldset>
<!-- image properties -->
<div id="controls">
	<table class="inputTable">
		<tr>
			<td style="text-align: right;" nowrap="nowrap"><label for="f_url"><?php if($insertMode=='image') echo 'File Name'; else echo 'URL';?></label></td>
			<td colspan="5"><input type="text" id="<?php if($insertMode=='image') echo 'f_url'; else echo 'f_href';?>" class="largelWidth" value="" /></td>
            <td rowspan="<?php echo $num_rows ?>" colspan="2" style="vertical-align: top; text-align: center;"><?php if($insertMode=='image') { ?>
            <div style="padding:4px;background-color:#CCC;border:1px inset;width: 100px; height: 100px;">
            <img src="<?php print $IMConfig['base_url'];?>img/1x1_transparent.gif" alt="" id="f_preview" />
            </div>
            <?php } else if($insertMode=="link" && $IMConfig['link_enable_target'] !== false) {?><label for="f_align" id="f_target_label">Target Window</label>
			<select id="f_target" style="width:125px;">
			  <option value="">None (use implicit)</option>
			  <option value="_blank">New window (_blank)</option>
			  <option value="_self">Same frame (_self)</option>
		      <option value="_top">Top frame (_top)</option>
		    </select><br /><br />
<input type="text" name="f_other_target" id="f_other_target" style="visibility:hidden; width:120px;" />
            <?php } ?></td>
            </tr>
<?php if($insertMode == 'image' && $IMConfig['images_enable_alt']) { ?>
		<tr>
			<td style="text-align: right;"><label for="f_alt">Alt</label></td>
			<td colspan="5"><input type="text" id="f_alt" class="largelWidth" value="" /></td>
        </tr>
<?php }
      if ($insertMode == 'link' || $IMConfig['images_enable_title']) { ?>
      <tr>
			<td style="text-align: right;"><label for="f_title">Title (tooltip)</label></td>
			<td colspan="5"><input type="text" id="f_title" class="largelWidth" value="" /></td>
      </tr>
<?php } ?>
		<tr>
<?php
if (!empty($IMConfig['max_foldersize_mb']) && Files::dirSize($manager->getImagesDir()) > ($IMConfig['max_foldersize_mb']*1048576))
{ ?>
	<td colspan="6" style="text-align: right;">Maximum folder size limit reached. Upload disabled.</td>
<?php }
else if($IMConfig['allow_upload']) { ?>
			<td style="text-align: right;"><label for="upload">Upload</label></td>
			<td colspan="5">
				<table cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td><input type="hidden" name="MAX_FILE_SIZE" value="<?php echo $max = (($insertMode == 'image' ? $IMConfig['max_filesize_kb_image'] : $IMConfig['max_filesize_kb_link'] )*1024); ?>" />
<input type="file" name="upload" id="upload" /></td>
                    <td><button type="submit" name="submit" onclick="doUpload();">Upload</button>(<?php echo $max/1024 . 'KB'?> max.)</td>
                  </tr>
                </table>
			</td>
<?php } else { ?>
			<td colspan="6"></td>
<?php } ?>
		</tr>
		<tr>
		 <td><?php if (!empty($hidden_fields)) foreach ($hidden_fields as $hf) echo "<input type=\"hidden\" id=\"{$hf}\" name=\"{$hf}\" value=\"\" />"; ?></td>
		 <td colspan="5"><span id="diskmesg"></span></td>
      </tr>
<tr>
			<td style="text-align: right;"><?php if($insertMode=='image') { ?> <label for="f_width">Width</label><?php }?></td>

			<td><?php if($insertMode=='image') { ?> <input type="text" id="f_width" class="smallWidth" value="" onchange="javascript:checkConstrains('width');"/><?php } else echo "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";?></td>

			<td rowspan="2"><?php if($insertMode=='image') { ?><img src="<?php print $IMConfig['base_url'];?>img/locked.gif" id="imgLock" width="25" height="32" alt="Constrained Proportions" />
				<input type="hidden" id="orginal_width" />
				<input type="hidden" id="orginal_height" />
            <input type="checkbox" id="constrain_prop" checked="checked" onclick="javascript:toggleConstrains(this);" value="on" /><br />
            <label for="constrain_prop">Constrain Proportions</label><?php }?>
            </td>

			<td rowspan="3" style="text-align: right;"></td>

			<td style="text-align: right;"><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><label for="f_margin">Margin</label><?php }?></td>

			<td><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><input type="text" id="f_margin" class="smallWidth" value="" /><?php } ?></td>
</tr>
<tr>
			<td style="text-align: right;"><?php if($insertMode=='image') { ?><label for="f_height">Height</label><?php }?></td>

			<td class="smallWidth"><?php if($insertMode=='image') { ?><input type="text" id="f_height" class="smallWidth" value="" onchange="javascript:checkConstrains('height');"/><?php }?></td>

			<td style="text-align: right;"><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><label for="f_padding">Padding</label><?php }?></td>

			<td><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><input type="text" id="f_padding" class="smallWidth" value="" />
			<?php }?></td>

            <?php if($insertMode=='image' && !empty($IMConfig['use_color_pickers']) && $IMConfig['images_enable_styling'] !== false) { ?>
   	            <td style="text-align: left;">Color</td>
  	            <td>
                  <input name="f_backgroundColor" type="text" id="f_backgroundColor" size="7" />
                </td>
  	        <?php } ?>
</tr>
<tr>
			<td style="text-align: right;"><?php if($insertMode=='image' && $IMConfig['images_enable_align'] !== false) { ?><label for="f_align">Align</label><?php }?></td>

			<td colspan="2"><?php if($insertMode=='image' && $IMConfig['images_enable_align'] !== false) { ?>
				<select size="1" id="f_align"  title="Positioning of this image">
				  <option value="" selected="selected"         >Not set</option>
				  <option value="left"                         >Left</option>
				  <option value="right"                        >Right</option>
				  <option value="texttop"                      >Texttop</option>
				  <option value="absmiddle"                    >Absmiddle</option>
				  <option value="baseline"                     >Baseline</option>
				  <option value="absbottom"                    >Absbottom</option>
				  <option value="bottom"                       >Bottom</option>
				  <option value="middle"                       >Middle</option>
				  <option value="top"                          >Top</option>
				</select><?php } ?>
			</td>

			<td style="text-align: right;"><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><label for="f_border">Border</label><?php }?></td>
			<td><?php if($insertMode=='image' && $IMConfig['images_enable_styling'] !== false) { ?><input type="text" id="f_border" class="smallWidth" value="" /><?php }?></td>
			<?php if($insertMode=='image' && !empty($IMConfig['use_color_pickers']) && $IMConfig['images_enable_styling'] !== false) { ?>
  	        <td style="text-align: left;">Border Color</td>
            <td><input name="f_borderColor" type="text" id="f_borderColor" size="7" /></td>
            <?php } ?>
</tr>
</table>

<!--// image properties -->	
	<div style="text-align: right;"> 
          <hr />
		  <button type="button" class="buttons" onclick="return refresh();">Refresh</button>
          <button type="button" class="buttons" onclick="return onOK();">OK</button>
          <button type="button" class="buttons" onclick="return onCancel();">Cancel</button>
    </div>
</div>
</form>
</body>
</html>
