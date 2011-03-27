<?php
/**
 * ExtendedFileManager configuration file.
 * Authors: Wei Zhuo, Afru
 * Version: Updated on 08-01-2005 by Afru
 * Version 1.1.2: Updated on 04-07-2006 by Krzysztof Kotowicz <koto@webworkers.pl>
 * Package: ExtendedFileManager
 * http://www.afrusoft.com/htmlarea
 */

/*  Configuration file usage:
 *	There are two insertModes for this filemanager.
 *	One is "image" and another is "link".
 *	So you can assign config values as below
 *
 *	if($insertMode=="image") $IMConfig['property']=somevalueforimagemode;
 *	else if($insertMode=="link") $IMConfig['property']=somevalueforlinkmode;
 *
 *	(or) you can directly as $IMConfig['property']=somevalueforbothmodes;
 *
 *	Best of Luck :) Afru.
 */
 
/*
 *	Getting the mode for further differentiation
 */

if(isset($_REQUEST['mode'])) $insertMode=$_REQUEST['mode'];
	if(!isset($insertMode)) $insertMode="image";

/**
* Default backend URL
*
* URL to use for unified backend.
*
* The ?__plugin=ExtendedFileManager& is required.
*/

$IMConfig['backend_url'] = "backend.php?__plugin=ExtendedFileManager&";

/**
* Backend Installation Directory
*
* location of backend install; these are used to link to css and js
* assets because we may have the front end installed in a different
* directory than the backend. (i.e. nothing assumes that the frontend
* and the backend are in the same directory)
*/
$IMConfig['base_dir'] = getcwd();
$IMConfig['base_url'] = '';


/*
	 File system path to the directory you want to manage the images
	 for multiple user systems, set it dynamically.

	 NOTE: This directory requires write access by PHP. That is,
		   PHP must be able to create files in this directory.
		   Able to create directories is nice, but not necessary.
*/
$IMConfig['images_dir'] = 'demo_images';
//You may set a different directory for the link mode; if you don't, the above setting will be used for both modes
//$IMConfig['files_dir'] = 'demo_files';

/*
 The URL to the above path, the web browser needs to be able to see it.
 Please remove scripting capabilities in this directory
 for this directory (i.e. disable PHP, Perl, CGI; see .htaccess file in demo_images folder).
*/
$IMConfig['images_url'] = str_replace( array("backend.php","manager.php"), "", $_SERVER["PHP_SELF"] ) . $IMConfig['images_dir'];
//$IMConfig['files_url'] = 'url/to/files_dir';

/*
  Format of the Date Modified in list view.
  It has to be a string understood by the PHP date() function (for possible values see http://http://php.net/manual/en/function.date.php)
*/
$IMConfig['date_format'] = "d.m.y H:i";
/*
  Possible values: true, false

  TRUE - If PHP on the web server is in safe mode, set this to true.
         SAFE MODE restrictions: directory creation will not be possible,
		 only the GD library can be used, other libraries require
		 Safe Mode to be off.

  FALSE - Set to false if PHP on the web server is not in safe mode.
*/
$IMConfig['safe_mode'] = false;

/*
This specifies whether any image library is available to resize and edit images.TRUE - Thumbnails will be resized by image libraries and if there is no library, default thumbnail will be shown.
FALSE - Thumbnails will be resized by browser ignoring image libraries.
*/
$IMConfig['img_library'] = true;


/*
View type when the File manager is in insert image mode.
Valid values are "thumbview" and "listview".
*/

    
if ($insertMode == 'image')
	$IMConfig['view_type'] = "thumbview";
	
else if($insertMode == "link")
	$IMConfig['view_type'] = "listview";

$IMConfig['insert_mode'] = $insertMode;

/* 
 Possible values: 'GD', 'IM', or 'NetPBM'

 The image manipulation library to use, either GD or ImageMagick or NetPBM.
 If you have safe mode ON, or don't have the binaries to other packages, 
 your choice is 'GD' only. Other packages require Safe Mode to be off.
*/
define('IMAGE_CLASS', 'GD');


/*
 After defining which library to use, if it is NetPBM or IM, you need to
 specify where the binary for the selected library are. And of course
 your server and PHP must be able to execute them (i.e. safe mode is OFF).
 GD does not require the following definition.
*/
define('IMAGE_TRANSFORM_LIB_PATH', '/usr/bin/');
//define('IMAGE_TRANSFORM_LIB_PATH', 'C:/"Program Files"/ImageMagick-5.5.7-Q16/');


/*
  The prefix for thumbnail files, something like .thumb will do. The
  thumbnails files will be named as "prefix_imagefile.ext", that is,
  prefix + orginal filename.
*/
$IMConfig['thumbnail_prefix'] = 't_';


/*
  Thumbnail can also be stored in a directory, this directory
  will be created by PHP. If PHP is in safe mode, this parameter
  is ignored, you can not create directories.

  If you do not want to store thumbnails in a directory, set this
  to false or empty string '';
*/
$IMConfig['thumbnail_dir'] = 't';

/**
* Resized prefix
*
* The prefix for resized files, something like .resized will do.  The
* resized files will be named <prefix>_<width>x<height>_<original>
* resized files are created when one changes the dimensions of an image
* in the image manager selection dialog - the image is scaled when the
* user clicks the ok button.
*/

$IMConfig['resized_prefix'] = '.resized';

// -------------------------------------------------------------------------

/**
* Resized Directory
*
* Resized images may also be stored in a directory, except in safe mode.
*/

$IMConfig['resized_dir'] = '';

/*
  Possible values: true, false

 TRUE -  Allow the user to create new sub-directories in the
         $IMConfig['images_dir']/$IMConfig['files_dir'].

 FALSE - No directory creation.

 NOTE: If $IMConfig['safe_mode'] = true, this parameter
       is ignored, you can not create directories
*/
$IMConfig['allow_new_dir'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to edit image by image editor.

 FALSE - No edit icon will be displayed.

 NOTE: If $IMConfig['img_library'] = false, this parameter
       is ignored, you can not edit images.
*/
$IMConfig['allow_edit_image'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to rename files and folders.

 FALSE - No rename icon will be displayed.

*/
$IMConfig['allow_rename'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to perform cut/copy/paste actions.

 FALSE - No cut/copy/paste icons will be displayed.

*/
$IMConfig['allow_cut_copy_paste'] = true;

/*
  Possible values: true, false

  TRUE - Display color pickers for image background / border colors

  FALSE - Don't display color pickers
*/
$IMConfig['use_color_pickers'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to set alt (alternative text) attribute.

 FALSE - No input field for alt attribute will be displayed.

 NOTE: The alt attribute is _obligatory_ for images, so <img alt="" /> will be inserted
      if 'images_enable_alt' is set to false
*/
$IMConfig['images_enable_alt'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to set title attribute (usually displayed when mouse is over element).

 FALSE - No input field for title attribute will be displayed.

*/
$IMConfig['images_enable_title'] = false;

/*
  Possible values: true, false

 TRUE -  Allow the user to set align attribute.

 FALSE - No selection box for align attribute will be displayed.

*/
$IMConfig['images_enable_align'] = true;

/*
  Possible values: true, false

 TRUE -  Allow the user to set margin, padding, and border styles for the image

 FALSE - No styling input fields will be displayed.

*/
$IMConfig['images_enable_styling'] = true;

/*
  Possible values: true, false

 TRUE -   Allow the user to set target attribute for link (the window in which the link will be opened).

 FALSE - No selection box for target attribute will be displayed.

*/
$IMConfig['link_enable_target'] = true;
/*
  Possible values: true, false

  TRUE - Allow the user to upload files.

  FALSE - No uploading allowed.
*/
$IMConfig['allow_upload'] = false;

/* Maximum upload file size

  Possible values: number, "max"

  number - maximum size in Kilobytes.

  "max"  - the maximum allowed by the server (the value is retrieved from the server configuration).
*/
$IMConfig['max_filesize_kb_image'] = 200;

$IMConfig['max_filesize_kb_link'] = 5000;

/* Maximum upload folder size in Megabytes. Use 0 to disable limit */
$IMConfig['max_foldersize_mb'] = 0;

/*
Allowed extensions that can be shown and allowed to upload.
Available icons are for "doc,fla,gif,gz,html,jpg,js,mov,pdf,php,png,ppt,rar,txt,xls,zip"
-Changed by AFRU.
*/

$IMConfig['allowed_image_extensions'] = array("jpg","gif","png","bmp");
$IMConfig['allowed_link_extensions'] = array("jpg","gif","js","php","pdf","zip","txt","psd","png","html","swf","xml","xls","doc");


/*
 The default thumbnail and list view icon in case thumbnails are not created and the files are of unknown.
*/
$IMConfig['default_thumbnail'] = 'icons/def.gif';
$IMConfig['default_listicon'] = 'icons/def_small.gif';


/*
Only files with these extensions will be shown as thumbnails. All other files will be shown as icons.
*/
$IMConfig['thumbnail_extensions'] = array("jpg", "gif", "png", "bmp");

/*
  Thumbnail dimensions.
*/
$IMConfig['thumbnail_width'] = 84;
$IMConfig['thumbnail_height'] = 84;

/*
  Image Editor temporary filename prefix.
*/
$IMConfig['tmp_prefix'] = '.editor_';


// Standard PHP Backend Data Passing
//  if data was passed using xinha_pass_to_php_backend() we merge the items
//  provided into the Config
require_once(realpath(dirname(__FILE__) . '/../../contrib/php-xinha.php'));
if($passed_data = xinha_read_passed_data())
{
  $IMConfig = array_merge($IMConfig, $passed_data);
  $IMConfig['backend_url'] .= xinha_passed_data_querystring() . '&';
}
// Deprecated config passing, don't use this way any more!
elseif(isset($_REQUEST['backend_config']))
{
  if(get_magic_quotes_gpc()) {
    $_REQUEST['backend_config'] = stripslashes($_REQUEST['backend_config']);
  }

  // Config specified from front end, check that it's valid
  session_start();
  if (!array_key_exists($_REQUEST['backend_config_secret_key_location'], $_SESSION))
    die("Backend security error.");

  $secret = $_SESSION[$_REQUEST['backend_config_secret_key_location']];

  if($_REQUEST['backend_config_hash'] !== sha1($_REQUEST['backend_config'] . $secret))
  {
    die("Backend security error.");
  }

  $to_merge = unserialize($_REQUEST['backend_config']);
  if(!is_array($to_merge))
  {
    die("Backend config syntax error.");
  }

  $IMConfig = array_merge($IMConfig, $to_merge);

   // changed config settings keys in relation to ImageManager
  $IMConfig['backend_url'] .= "backend_config=" . rawurlencode($_REQUEST['backend_config']) . '&';
  $IMConfig['backend_url'] .= "backend_config_hash=" . rawurlencode($_REQUEST['backend_config_hash']) . '&';
  $IMConfig['backend_url'] .= "backend_config_secret_key_location=" . rawurlencode($_REQUEST['backend_config_secret_key_location']) . '&';

}
if ($IMConfig['max_filesize_kb_link'] == "max")
{
  $IMConfig['max_filesize_kb_link'] = upload_max_filesize_kb();
}

if ($IMConfig['max_filesize_kb_image'] == "max")
{
  $IMConfig['max_filesize_kb_image'] = upload_max_filesize_kb();
}
// END

?>
