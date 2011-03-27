<?php
/**
 * The main GUI for the ImageManager.
 * @author $Author:ray $
 * @version $Id:manager.php 987 2008-04-12 12:39:04Z ray $
 * @package ImageManager
 */

	require_once('config.inc.php');
	require_once('ddt.php');
	require_once('Classes/ImageManager.php');
	
	$manager = new ImageManager($IMConfig);
	$dirs = $manager->getDirs();

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
<head>
	<title>Insert Image</title>
  <script type="text/javascript">
    // temporary. An ImageManager rewrite will take care of this kludge.
    _backend_url = "<?php print $IMConfig['backend_url']; ?>";
    _resized_prefix = "<?php echo $IMConfig['resized_prefix']; ?>";
    _resized_dir = "<?php echo $IMConfig['resized_dir']; ?>";
  </script>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
 <link href="<?php print $IMConfig['base_url'];?>assets/manager.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="../../popups/popup.js"></script>
<script type="text/javascript" src="assets/popup.js"></script>
<script type="text/javascript" src="../../modules/ColorPicker/ColorPicker.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/dialog.js"></script>
<script type="text/javascript">
/*<![CDATA[*/
	if(window.opener)
		Xinha = HTMLArea = window.opener.Xinha;

	var thumbdir = "<?php echo $IMConfig['thumbnail_dir']; ?>";
	var base_url = "<?php echo $manager->getImagesURL(); ?>";
/*]]>*/
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/manager.js"></script>
<?php
  if(!$IMConfig['show_full_options'])
  {
    ?>
    <style type="text/css">
      .fullOptions { visibility:hidden; }
    </style>
    <?php
  }
?>
</head>
<body>

<form action="<?php print $IMConfig['backend_url'] ?>" id="uploadForm" method="post" enctype="multipart/form-data">

<input type="hidden" name="__plugin" value="ImageManager" />
<input type="hidden" name="__function" value="images" />

<fieldset>
  <legend>Image Manager</legend>
  <table width="100%">
    <tr>
      <th><label for="dirPath">Directory</label></th>
      <td>
        <select name="dir" class="dirWidth" id="dirPath" onchange="updateDir(this)">
          <option value="/">/</option>
          <?php
            foreach($dirs as $relative=>$fullpath)
            {
              ?>
              <option value="<?php echo rawurlencode($relative); ?>"><?php echo $relative; ?></option>
              <?php
            }
          ?>
        </select>
      </td>
      <td>
        <a href="#" onclick="javascript: goUpDir();" title="Directory Up"><img src="<?php print $IMConfig['base_url']; ?>img/btnFolderUp.gif" height="15" width="15" alt="Directory Up" /></a>

        <?php
          if($IMConfig['safe_mode'] == false && $IMConfig['allow_new_dir'])
          {
            ?>
            <a href="#" onclick="newFolder();" title="New Folder"><img src="<?php print $IMConfig['base_url']; ?>img/btnFolderNew.gif" height="15" width="15" alt="New Folder" /></a>
            <?php
          }
          ?>
      </td>
    </tr>
    <?php
      if($IMConfig['allow_upload'] == TRUE)
      {
        ?>
        <tr>
          <th style="text-align: left;">Upload:</th>
          <td colspan="2">
            <input type="file" name="upload" id="upload" />
            <input name="Upload" type="submit" id="Upload" value="Upload" onclick="doUpload();" />
          </td>
        </tr>
        <?php
      }
    ?>

  </table>

  <div id="messages" style="display: none;"><span id="message"></span><img src="<?php print $IMConfig['base_url']; ?>img/dots.gif" width="22" height="12" alt="..." /></div>

  <iframe src="<?php print $IMConfig['backend_url']; ?>__function=images" name="imgManager" id="imgManager" class="imageFrame" scrolling="auto" title="Image Selection" frameborder="0"></iframe>

</fieldset>

<!-- image properties -->

<table  border="0" cellspacing="0" cellpadding="0" width="100%">
  <tr>
    <th style="text-align: left;">Description:</th>
    <td colspan="6">
      <input type="text" id="f_alt" style="width:95%"/>
    </td>
    <td rowspan="4" width="100" height="100" style="vertical-align: middle;" style="padding:4px;background-color:#CCC;border:1px inset;">
      <img src="" id="f_preview" />
    </td>
  </tr>

  <tr>
    <th style="text-align: left;">Width:</th>
    <td >
      <input id="f_width" type="text" name="f_width" size="4" onchange="javascript:checkConstrains('width');" />
    </td>
    <td rowspan="2">
      <div  style="position:relative">
        <img src="<?php print $IMConfig['base_url']; ?>img/locked.gif" id="imgLock" width="25" height="32" alt="Constrained Proportions" style="vertical-align: middle;" /><input type="checkbox" id="constrain_prop" checked="checked" onclick="javascript:toggleConstrains(this);" style="position:absolute;top:8px;left:0px;" value="on" />
      </div>
    </td>
    <th style="text-align: left;" class="fullOptions">Margin:</th>
    <td colspan="3" class="fullOptions">
      <input name="f_margin" type="text" id="f_margin" size="3" />
      px </td>
  </tr>

  <tr>
    <th style="text-align: left;">Height:</th>
    <td>
      <input name="f_height" type="text" id="f_height" size="4" />
    </td>
    <th style="text-align: left;" class="fullOptions">Padding:</th>
    <td  class="fullOptions">
      <input name="f_padding" type="text" id="f_padding" size="3" />
      px </td>
    <th style="text-align: left;" class="fullOptions">Color:</th>
    <td  class="fullOptions">
      <input name="f_backgroundColor" type="text" id="f_backgroundColor" size="7" />
     
    </td>
  </tr>


  <tr class="fullOptions">
    <th style="text-align: left;">Alignment:</th>
    <td colspan="2">
      <select size="1" id="f_align" title="Positioning of this image">
        <option value=""                             >Not set</option>
        <option value="left"                         >Left</option>
        <option value="right"                        >Right</option>
        <option value="texttop"                      >Texttop</option>
        <option value="absmiddle"                    >Absmiddle</option>
        <option value="baseline" selected="selected" >Baseline</option>
        <option value="absbottom"                    >Absbottom</option>
        <option value="bottom"                       >Bottom</option>
        <option value="middle"                       >Middle</option>
        <option value="top"                          >Top</option>
      </select>
    </td>
    <th style="text-align: left;">Border:</th>
    <td>
      <input name="f_border" type="text" id="f_border" size="3" />
      px </td>
    <th style="text-align: left;">Color:</th>
    <td>
      <input name="f_borderColor" type="text" id="f_borderColor" size="7" />
      
    </td>
  </tr>

</table>

<div style="text-align: right;">
  <hr />
  <button type="button" class="buttons" onclick="return refresh();">Refresh</button>
  <button type="button" class="buttons" onclick="return onOK();">OK</button>
  <button type="button" class="buttons" onclick="return onCancel();">Cancel</button>
</div>

<!--// image properties -->
<input type="hidden" id="orginal_width" />
<input type="hidden" id="orginal_height" />
<input type="hidden" id="f_url" class="largelWidth" value="" />
</form>
</body>
</html>
