Package : Extended File Manager EFM 1.1.1

Version 1.1 created from 1.0 beta by Krzysztof Kotowicz <koto@webworkers.pl>

Overview :
----------

Extended File Manager is an advanced plugin for Xinha 

It works in two different modes.
1). Insert Image Mode and 
2). Insert File Link Mode.

In Insert Image Mode, it replaces the basic insert image functionality of Xinha with its advanced image manager.

If Insert File Link Mode is enabled, a new icon will be added to the toolbar with advanced file linking capability.



Complete Features :
-------------------
* Easy config.inc file that enables individual options for both modes.
* Thumnail View 
* List View 
* Nice icons for both views 
* Create Folders 
* Vertical Scrolling 
* Allowed extensions to view or upload.
* File Uploads 
* Max File upload limit 
* Max Upload Folder size (Including all subfolders and files. A must see option.)
* Dynamic display of available free space in the Upload Folder 
* Dynamic Thumbnails using Image libraries or browser resize 
* Image Editor (Actually done by Wei...a great addon) 
* Can be used to insert images along with properties. 
* Can be used to insert link to non-image files like pdf or zip.
* You can specify image margin / padding / background and border colors
* You may edit Alt/title tags for inserted images

(Most of the features can be enabled/disabled as needed)

Installation :
--------------

Installing involves extracting the archive to 'plugins' subdirectory of Xinha
and selecting the plugin in appropriate xinha_plugins list.

Plugin may be configured via xinha_config.ExtendedFileManager object.
Look into ImageManager plugin documentation as this plugin uses almost identical
settings. All available options can be found in the file config.inc.php.

// only snippets of code from initializing file shown below


  xinha_plugins = xinha_plugins ? xinha_plugins :
  [
   'ContextMenu',
   'SuperClean',
   'CharacterMap',
   'GetHtml',
   'ExtendedFileManager',
   /*'ImageManager',*/  // replace image manager with EFM
   'Linker'
  ];

...

//If you don't want to add a button for linking files and use only the advanced ImageManager
xinha_config.ExtendedFileManager.use_linker = false;
// pass the configuration to plugin
if (xinha_config.ExtendedFileManager) {
   	    with (xinha_config.ExtendedFileManager)
        {
            <?php

            // define backend configuration for the plugin
            $IMConfig = array();
            $IMConfig['images_dir'] = '<images dir>';
            $IMConfig['images_url'] = '<images url>';
            $IMConfig['files_dir'] = '<files dir>';
            $IMConfig['files_url'] = '<files url>';
            $IMConfig['thumbnail_prefix'] = 't_';
            $IMConfig['thumbnail_dir'] = 't';
            $IMConfig['resized_prefix'] = 'resized_';
            $IMConfig['resized_dir'] = '';
            $IMConfig['tmp_prefix'] = '_tmp';
            $IMConfig['max_filesize_kb_image'] = 2000;
            // maximum size for uploading files in 'insert image' mode (2000 kB here)

            $IMConfig['max_filesize_kb_link'] = 5000;
            // maximum size for uploading files in 'insert link' mode (5000 kB here)

            // Maximum upload folder size in Megabytes.
            // Use 0 to disable limit
            $IMConfig['max_foldersize_mb'] = 0;
            
            $IMConfig['allowed_image_extensions'] = array("jpg","gif","png");
            $IMConfig['allowed_link_extensions'] = array("jpg","gif","pdf","ip","txt",
                                                         "psd","png","html","swf",
                                                         "xml","xls");

            require_once '/path/to/xinha/contrib/php-xinha.php';
            xinha_pass_to_php_backend($IMConfig);
            
            ?>
        }
}

=====
afrusoft@gmail.com - author of EFM 1.0 beta
koto@webworkers.pl - EFM 1.1 (most of the code taken from Xinha codebase)