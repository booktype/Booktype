<?PHP
  //this plugin only use the relativ webpath to the picturefolder
  //default ~  /Xinha/plugins/InsertPicture/demo_pictures/
  strstr( PHP_OS, "WIN") ? $strPathSeparator = "\\" : $strPathSeparator = "/";
  if (isset($_REQUEST['picturepath'])) {
    $PicturePath = $_REQUEST['picturepath'];

    $AInsertPicturePath = explode ('/', dirname($_SERVER['PHP_SELF']));
    $ALocalInsertPicturePath = explode($strPathSeparator, dirname(__FILE__));
    $AtheRootPath = array_values (array_diff ($ALocalInsertPicturePath, $AInsertPicturePath));
    $RootPath = implode($strPathSeparator, $AtheRootPath);

    $LocalPicturePath = str_replace('http://'.$_SERVER['HTTP_HOST'], "", $PicturePath);
    $LocalPicturePath = str_replace('/', $strPathSeparator, $LocalPicturePath);
    $LocalPicturePath = $RootPath.$LocalPicturePath;

    $LocalPicturePath = dirname(__FILE__).$strPathSeparator.'demo_pictures'.$strPathSeparator;
    //$LocalPicturePath = realpath('../../../../images/content/').$strPathSeparator;
  }
  $limitedext = array(".gif",".jpg",".png",".jpeg"); //Extensions you want files uploaded limited to.
  $limitedsize = "1000000"; //size limit in bytes
  $message = "";

  function formatSize($size)
  {
    if($size < 1024)
      return $size.' bytes';
    else if($size >= 1024 && $size < 1024*1024)
      return sprintf('%01.2f',$size/1024.0).' Kb';
    else
      return sprintf('%01.2f',$size/(1024.0*1024)).' Mb';
  }
  $DestFileName = "";
  if (isset($_FILES['file'])) {
    $file = $_FILES['file'];
    $ext = strrchr($file['name'],'.');
    if (!in_array($ext,$limitedext))
      $message = "The file you are uploading doesn't have the correct extension.";
    else if (file_exists($LocalPicturePath.$file['name']))
      $message = "The file you are uploading already exists.";
    else if ($file['size'] > $limitedsize)
      $message = "The file you are uploading is to big. The max Filesize is</span><span> ".formatSize($limitedsize).".";
    else
      copy($file['tmp_name'], $LocalPicturePath.$file['name']);
    $DestFileName = $file['name'];
  }
?>
<html>
<head>
  <title>Insert Image</title>
<link rel="stylesheet" type="text/css" href="../../popups/popup.css" />
<script type="text/javascript" src="../../popups/popup.js"></script>

<script type="text/javascript">
  window.resizeTo(500, 490);
var Xinha = window.opener.Xinha;
function i18n(str) {
  return (Xinha._lc(str, 'Xinha'));
}

function Init() {
  __dlg_translate("InsertPicture");
  __dlg_init();

  // Make sure the translated string appears in the drop down. (for gecko)
  document.getElementById("f_align").selectedIndex = 0;
  document.getElementById("f_align").selectedIndex = document.getElementById("f_align").selectedIndex;
  var param = window.dialogArguments;
  if (param) {
      document.getElementById("f_url").value = param["f_url"];
      document.getElementById("f_alt").value = param["f_alt"];
      document.getElementById("f_border").value = param["f_border"];
      document.getElementById("f_align").value = param["f_align"];
      document.getElementById("f_vert").value = (param["f_vert"]!="-1") ? param["f_vert"] : "";
      document.getElementById("f_horiz").value = (param["f_horiz"]!="-1") ? param["f_horiz"] : "";
      document.getElementById("f_height").value = param["f_height"];
      document.getElementById("f_width").value = param["f_width"];
      window.ipreview.location.replace(param.f_url);
  }
  document.getElementById("f_url").focus();
  document.getElementById("filelist").selectedIndex = document.getElementById("filelist").selectedIndex;
<?php If ($DestFileName<>"")
  echo "CopyToURL(\"".$PicturePath.$DestFileName."\");"
?>
}

function onOK() {
  var required = {
    "f_url": i18n("You must enter the URL")
  };
  for (var i in required) {
    var el = document.getElementById(i);
    if (!el.value) {
      alert(required[i]);
      el.focus();
      return false;
    }
  }
  // pass data back to the calling window
  var fields = ["f_url", "f_alt", "f_align", "f_border", "f_horiz", "f_vert", "f_width", "f_height"];
  var param = new Object();
  for (var i in fields) {
    var id = fields[i];
    var el = document.getElementById(id);
    param[id] = el.value;
  }
  __dlg_close(param);
  return false;
}

function onUpload() {
  var required = {
    "file": i18n("Please select a file to upload.")
  };
  for (var i in required) {
    var el = document.getElementById(i);
    if (!el.value) {
      alert(required[i]);
      el.focus();
      return false;
    }
  }
  return true;
}

function onCancel() {
  __dlg_close(null);
  return false;
}

function onPreview() {
  var f_url = document.getElementById("f_url");
  var url = f_url.value;
  if (!url) {
    alert(i18n("You must enter the URL"));
    f_url.focus();
    return false;
  }
  if (document.all) {
    window.ipreview.location.replace('viewpicture.html?'+url);
  } else {
    window.ipreview.location.replace(url);
  }
  return false;
}

var img = new Image();
function imgWait() {
  waiting = window.setInterval("imgIsLoaded()", 1000)
}
function imgIsLoaded() {
  if(img.width > 0) {
    window.clearInterval(waiting)
    document.getElementById("f_width").value = img.width;
    document.getElementById("f_height").value = img.height;
  }
}

function CopyToURL(imgName) {
  document.getElementById("f_url").value = imgName;
  onPreview();
  img.src = imgName;
  img.onLoad = imgWait()
}

function openFile() {
  window.open(document.getElementById("f_url").value,'','');
}
</script>
</head>
<body class="dialog" onload="Init()">
<div class="title">Insert Image</div>
<table border="0" width="100%" style="padding: 0px; margin: 0px">
  <tbody>
  <tr>
    <td>Images on the Server:<?php /*echo $LocalPicturePath*/ ?><br>
    <select id="filelist" name="filelist" style="width:200" size="10" onClick="CopyToURL(this[this.selectedIndex].value);">
<?php
  $d = @dir($LocalPicturePath);
  while (false !== ($entry = $d->read())) {
    if(substr($entry,0,1) != '.') {  //not a dot file or directory
      if ($entry == $DestFileName)
        echo '<OPTION value="' . $PicturePath.$entry. '" selected="selected">' . $entry . '(' . formatSize(filesize($LocalPicturePath.'\\'.$entry)) .')</OPTION>';
      else
        echo '<OPTION value="' . $PicturePath.$entry. '">' . $entry . '(' . formatSize(filesize($LocalPicturePath.'\\'.$entry)) .')</OPTION>';
    }
  }
  $d->close();
?>
    </select>

      <form method="post" action="" enctype="multipart/form-data">
        <input type="hidden" name="localpicturepath" value="<?php echo $LocalPicturePath ?>">
        <input type="hidden" name="picturepath" value="<?php echo $PicturePath ?>">
        <input type="file" name="file" id="file" size="30"><br>
        <button type="submit" name="ok" onclick="onUpload();">Upload file</button><br>
        <span><?php echo $message ?></span>
      </form>

    </td>
    <td style="vertical-align: middle;" width="200" height="230">
    <span>Image Preview:</span>
    <a href="#" onClick="javascript:openFile();"title=" Open file in new window"><img src="img/btn_open.gif"  width="18" height="18" border="0" title="Open file in new window" /></a><br />
    <iframe name="ipreview" id="ipreview" frameborder="0" style="border : 1px solid gray;" height="200" width="200" src=""></iframe>
    </td>
  </tr>
  </tbody>
</table>

<form action="" method="get">
  <input type="hidden" name="localpicturepath" value="<?php echo $LocalPicturePath ?>">
  <input type="hidden" name="picturepath" value="<?php echo $PicturePath ?>">
<table border="0" width="100%" style="padding: 0px; margin: 0px">
  <tbody>

  <tr>
    <td style="width: 7em; text-align: right">Image URL:</td>
    <td><input type="text" name="url" id="f_url" style="width:75%"
      title="Enter the image URL here"  value="<?php echo $PicturePath.$DestFileName ?>"/>
      <button name="preview" onclick="return onPreview();"
      title="Preview the image in a new window">Preview</button>
    </td>
  </tr>
  <tr>
    <td style="width: 7em; text-align: right">Alternate text:</td>
    <td><input type="text" name="alt" id="f_alt" style="width:100%"
      title="For browsers that don't support images" /></td>
  </tr>

  </tbody>
</table>

<p />

<fieldset style="float: left; margin-left: 5px;">
<legend>Layout</legend>

<div class="space"></div>

<div class="fl" style="width: 6em;">Alignment:</div>
<select size="1" name="align" id="f_align"
  title="Positioning of this image">
  <option value=""                             >Not set</option>
  <option value="left"                         >Left</option>
  <option value="right"                        >Right</option>
  <option value="texttop"                      >Texttop</option>
  <option value="absmiddle"                    >Absmiddle</option>
  <option value="baseline"                     >Baseline</option>
  <option value="absbottom"                    >Absbottom</option>
  <option value="bottom"                       >Bottom</option>
  <option value="middle"                       >Middle</option>
  <option value="top"                          >Top</option>
</select>

<p />

<div class="fl" style="width: 6em;">Border thickness:</div>
<input type="text" name="border" id="f_border" size="5" title="Leave empty for no border" />
<div class="space"></div>

</fieldset>

<fieldset style="float: left; margin-left: 5px;">
<legend>Size</legend>

<div class="space"></div>

<div class="fl" style="width: 5em;">Width:</div>
<input type="text" name="width" id="f_width" size="5" title="Leave empty for not defined" />
<p />

<div class="fl" style="width: 5em;">Height:</div>
<input type="text" name="height" id="f_height" size="5" title="Leave empty for not defined" />
<div class="space"></div>

</fieldset>

<fieldset style="float:right; margin-right: 5px;">
<legend>Spacing</legend>

<div class="space"></div>

<div class="fr" style="width: 5em;">Horizontal:</div>
<input type="text" name="horiz" id="f_horiz" size="5" title="Horizontal padding" />
<p />

<div class="fr" style="width: 5em;">Vertical:</div>
<input type="text" name="vert" id="f_vert" size="5" title="Vertical padding" />

<div class="space"></div>

</fieldset>
<br clear="all" />

<div id="buttons">
  <button type="submit" name="ok" onclick="return onOK();">OK</button>
  <button type="button" name="cancel" onclick="return onCancel();">Cancel</button>
</div>
</form>
</body>
</html>