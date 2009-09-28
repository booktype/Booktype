<?php
/**
 * ExtendedFileManager editor.php file.
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

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
<head>
	<title>Xinha Image Editor</title>
	<link href="<?php print $IMConfig['base_url'];?>assets/editor.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/slider.js"></script>
<script type="text/javascript" src="../../popups/popup.js"></script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/popup.js"></script>
<script type="text/javascript">
/*<![CDATA[*/

    var _backend_url = "<?php print $IMConfig['backend_url']."&mode=$insertMode"; ?>&";

	if(window.opener)
		Xinha = window.opener.Xinha;
/*]]>*/
</script>
<script type="text/javascript" src="<?php print $IMConfig['base_url'];?>assets/editor.js"></script>
</head>

<body>
<table style="width:100%">
<tr>
	<td id="indicator">
    	<img src="<?php print $IMConfig['base_url'];?>img/spacer.gif" id="indicator_image" height="20" width="20" alt=""/>
	</td>
	<td id="tools">
		<div id="tools_crop" style="display:none;">
			<div class="tool_inputs">
				<label for="cx">Start X:</label><input type="text" id="cx"  class="textInput" onchange="updateMarker('crop')"/>
				<label for="cy">Start Y:</label><input type="text" id="cy" class="textInput" onchange="updateMarker('crop')"/>
				<label for="cw">Width:</label><input type="text" id="cw" class="textInput" onchange="updateMarker('crop')"/>
				<label for="ch">Height:</label><input type="text" id="ch" class="textInput" onchange="updateMarker('crop')"/>			<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
			</div>	
			<a href="javascript:void(0);" onclick="editor.doSubmit('crop');" class="buttons" title="OK"><img src="<?php print $IMConfig['base_url'];?>img/btn_ok.gif" height="30" width="30" alt="OK" /></a>
			<a href="javascript:void(0);" onclick="editor.reset();" class="buttons" title="Cancel"><img src="<?php print $IMConfig['base_url'];?>img/btn_cancel.gif" height="30" width="30" alt="Cancel" /></a>
		</div>	
		<div id="tools_scale" style="display:none;">
			<div class="tool_inputs">
				<label for="sw">Width:</label><input type="text" id="sw" class="textInput" onchange="checkConstrains('width')"/>
				<a href="javascript:void(0);" onclick="toggleConstraints();" title="Lock"><img src="<?php print $IMConfig['base_url'];?>img/islocked2.gif" id="scaleConstImg" height="14" width="8" alt="Lock" class="div" /></a><label for="sh">Height:</label>
				<input type="text" id="sh" class="textInput" onchange="checkConstrains('height')"/>
				<input type="checkbox" id="constProp" value="1" checked="checked" onclick="toggleConstraints()"/>
				<label for="constProp">Constrain Proportions</label>
				<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
			</div>	
			<a href="javascript:void(0);" onclick="editor.doSubmit('scale');" class="buttons" title="OK"><img src="<?php print $IMConfig['base_url'];?>img/btn_ok.gif" height="30" width="30" alt="OK" /></a>
			<a href="javascript:void(0);" onclick="zoom();" class="buttons" title="Cancel"><img src="<?php print $IMConfig['base_url'];?>img/btn_cancel.gif" height="30" width="30" alt="Cancel" /></a>
		</div>	
		<div id="tools_rotate" style="display:none;">
			<div class="tool_inputs">
				<select id="rotate_sub_action" name="rotate_sub_action" onchange="rotateSubActionSelect(this)" style="margin-left: 10px; vertical-align: middle;">
					<option selected="selected" value="rotate">Rotate Image</option>
					<option value="flip">Flip Image</option>
				</select>
				<select id="rotate_preset_select" name="rotate_preset_select" onchange="rotatePreset(this)" style="margin-left: 20px; vertical-align: middle;">
					<option>Preset</option>
					<option value="180">Rotate 180 &deg;</option>
					<option value="90">Rotate 90 &deg; CW</option>
					<option value="-90">Rotate 90 &deg; CCW</option>
				</select>
				<select id="flip" name="flip" style="margin-left: 20px; vertical-align: middle;display:none">
					<option value="hoz">Flip Horizontal</option>
					<option value="ver">Flip Vertical</option>
				</select>
				<label for="ra">Angle:<input type="text" id="ra" class="textInput" /></label>
				<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
			</div>	
			<a href="javascript:void(0);" onclick="editor.doSubmit('rotate');" class="buttons" title="OK"><img src="<?php print $IMConfig['base_url'];?>img/btn_ok.gif" height="30" width="30" alt="OK" /></a>
			<a href="javascript:void(0);" onclick="editor.reset();" class="buttons" title="Cancel"><img src="<?php print $IMConfig['base_url'];?>img/btn_cancel.gif" height="30" width="30" alt="Cancel" /></a>
		</div>		
		<div id="tools_measure" style="display:none;">
			<div class="tool_inputs">
				<label>X:</label><input type="text" class="measureStats" id="sx" />
				<label>Y:</label><input type="text" class="measureStats" id="sy" />
				<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
				<label>W:</label><input type="text" class="measureStats" id="mw" />
				<label>H:</label><input type="text" class="measureStats" id="mh" />
				<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
				<label>A:</label><input type="text" class="measureStats" id="ma" />		
				<label>D:</label><input type="text" class="measureStats" id="md" />		
				<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
				<button type="button" onclick="editor.reset();" >Clear</button>
			</div>	
		</div>
		<div id="tools_save" style="display:none;">
			<div class="tool_inputs">
				<label for="save_filename">Filename:</label><input type="text" id="save_filename" value="<?php echo $editor->getDefaultSaveFile();?>"/>
				<select name="format" id="save_format" style="margin-left: 10px; vertical-align: middle;" onchange="updateFormat(this)">
	            <option value="jpeg,85">JPEG High</option>
	            <option value="jpeg,60">JPEG Medium</option>
	            <option value="jpeg,35">JPEG Low</option>
	            <option value="png">PNG</option>
				<?php if($editor->isGDGIFAble() != -1) { ?>
	            <option value="gif">GIF</option>
				<?php } ?>
	         </select>
			 <div id="slider" style="display:inline">
				<label>Quality:</label>
				<table style="display: inline; vertical-align: middle;" cellpadding="0" cellspacing="0">
					<tr>
					<td>
						<div id="slidercasing"> 
					<div id="slidertrack" style="width:100px"><img src="<?php print $IMConfig['base_url'];?>img/spacer.gif" width="1" height="1" border="0" alt="track" /></div>
	            <div id="sliderbar" style="left:85px" onmousedown="captureStart();"><img src="<?php print $IMConfig['base_url'];?>img/spacer.gif" width="1" height="1" border="0" alt="track" /></div>
				</div>	
					</td>
					</tr>
				</table>
				<input type="text" id="quality" onchange="updateSlider(this.value)" style="width: 2em;" value="85"/>
			</div>
			<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
			<div style="display:inline;font-size:10px">
			<span>Filesize:</span> <span id="filesize"></span>
			</div> 
			<img src="<?php print $IMConfig['base_url'];?>img/div.gif" height="30" width="2" class="div" alt="|" />
			</div>	
			<button type="button" style="float:left;margin:17px 5px 0 ;" onclick="editor.doSubmit('preview')">Preview</button>
			<button type="button" style="float:left;margin-top:17px;" onclick="editor.doSubmit('save');">Save</button>
			</div>	
	</td>
</tr>
<tr>
	<td id="toolbar">
		<a href="javascript:void(0);"  onclick="toggle('crop')" id="icon_crop" title="Crop"><img src="<?php print $IMConfig['base_url'];?>img/crop.gif" height="20" width="20" alt="Crop" /><span>Crop</span></a>
		<a href="javascript:void(0);" onclick="toggle('scale')" id="icon_scale" title="Resize"><img src="<?php print $IMConfig['base_url'];?>img/scale.gif" height="20" width="20" alt="Resize" /><span>Resize</span></a>
		<a href="javascript:void(0);" onclick="toggle('rotate')" id="icon_rotate" title="Rotate"><img src="<?php print $IMConfig['base_url'];?>img/rotate.gif" height="20" width="20" alt="Rotate" /><span>Rotate</span></a>
		<a href="javascript:void(0);" onclick="toggle('measure')" id="icon_measure" title="Measure"><img src="<?php print $IMConfig['base_url'];?>img/measure.gif" height="20" width="20" alt="Measure" /><span>Measure</span></a>
		<a href="javascript:void(0);" onclick="toggleMarker();" title="Toggle marker color"><img id="markerImg" src="<?php print $IMConfig['base_url'];?>img/t_black.gif" height="20" width="20" alt="Marker" /><span>Marker</span></a>
		<a href="javascript:void(0);" onclick="toggle('save')" id="icon_save" title="Save"><img src="<?php print $IMConfig['base_url'];?>img/save.gif" height="20" width="20" alt="Save" /><span>Save</span></a>
		<div style="margin-top:10px">Zoom</div>
		<select id="zoom" onchange="zoom(this.value)">
			<option value="10">10%</option>
			<option value="25">25%</option>
			<option value="50">50%</option>
			<option value="75">75%</option>
			<option value="100" selected="selected">100%</option>
			<option value="200">200%</option>
		</select>
	</td>
	<td id="contents">
		<?php
		$iframe_src = $IMConfig['backend_url'].'__function=editorFrame&img='.((isset($_GET['img'])) ? rawurlencode($_GET['img']) : '').'&mode='. $insertMode;
		?>
		<iframe src="<?php print htmlspecialchars($iframe_src) ?>" name="editor" id="editor"  scrolling="auto" title="Image Editor" frameborder="0"></iframe>
	</td>
</tr>
</table>
</body>
</html>
