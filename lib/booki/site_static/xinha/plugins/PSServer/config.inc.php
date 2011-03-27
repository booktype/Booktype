<?php
/**
 * PersistentStorage Server backend configuration file.
 * @author Douglas Mayle <douglas@openplans.org>
 * @version 1.0
 * @package PersistentStorage
 */

/**
 * If this file is being requested over the web, we display a JSON version of
 * the publicly viewable config info.
 */
if (__FILE__ == $_SERVER['SCRIPT_FILENAME']) {
    echo json_encode(get_config());
}

/**
 * Gets the configuration information used by this package.
 * {@source }
 * @param boolean $getprivates Return private configuration info merged with the public.
 * @returns array The configuration information for this package.
 */
function get_config($getprivates=False) {

    // We set up two different settings array, so that we can have settings
    // that won't be shown to the public.
    $Private = array();
    $Public = array();

    /**
     * For demo purposes, we can lie to the frontend and pretend to have user
     * storage.  Since we don't have a password mechanism, this simulation will
     * accept any password.
     */
    $Private['simulate_user_auth'] = false;

    /**
     * The capabilities array contains directives about what major options to
     * allow or disallow.
     */
    $Public['capabilities'] = array(
        // Allow directory operations (e.g. rename, create, delete directories)
        'directory_operations' => true,
        // Allow file operations (e.g. copy, rename, delete files)
        'file_operations' => true,
        // Allow image operations (e.g. scale, rotate, convert images)
        'image_operations' => true,
        // Allow file uploads
        'upload_operations' => true,
        // Stored files have a published URL
        'shared_publish' => true,
        // By default, if the user is authenticated, we enable user storage.
        // Set to false to disable.
        'user_storage' => !empty($_SERVER['PHP_AUTH_USER']) || $Private['simulate_user_auth']
    );

    /**
     * Directory exposed to user operations.  Be sure that the web server has
     * read and write access to this directory.
     */
    $Private['storage_dir'] = 'demo_images';

    /**
     * The URL that the storage directory is exposed as.  By default, we try
     * and guess based on the URL used to access this page.  Also, since we
     * allow user upload, this directory should not be executable by the
     * server.  A sample .htaccess file is included in demo_images.
     */
    $Private['storage_url'] = str_replace( array("backend.php","manager.php"),
                          "", $_SERVER["PHP_SELF"] ) . $Private['storage_dir'];

    /*
      Possible values: true, false

      TRUE - If PHP on the web server is in safe mode, set this to true.
             SAFE MODE restrictions: directory creation will not be possible,
    		 only the GD library can be used, other libraries require
    		 Safe Mode to be off.

      FALSE - Set to false if PHP on the web server is not in safe mode.
    */
    $Private['safe_mode'] = ini_get('safe_mode');

    /**
     * If PHP Safe Mode is on than only the GD image library will function, so
     * we force the default
     */
    if ($Private['safe_mode']) {
        @define('IMAGE_CLASS', 'GD');
    } else {
        /* 
         Possible values: 'GD', 'IM', or 'NetPBM'

         The image manipulation library to use, either GD or ImageMagick or NetPBM.
        */
        @define('IMAGE_CLASS', 'GD');

        /*
         After defining which library to use, if it is NetPBM or IM, you need to
         specify where the binary for the selected library are. And of course
         your server and PHP must be able to execute them (i.e. safe mode is OFF).
         GD does not require the following definition.
        */
        @define('IMAGE_TRANSFORM_LIB_PATH', '/usr/bin/');
    }

    /*
      The prefix for thumbnail files, something like .thumb will do. The
      thumbnails files will be named as "prefix_imagefile.ext", that is,
      prefix + orginal filename.
    */
    $Private['thumbnail_prefix'] = 't_';

    /**
     * The thumbnail array groups all of the configuration related to thumbnail
     * operations.
     */
    $Private['thumbnails'] = array(
        // The prefix to apply to all created thumbnails.
        'prefix' => 't_',
        // A subdirectory to keep thumbnails in.  If this is empty, thumbnails
        // will be stored alongside the files.
        'directory' => '',
        // Whether or not to filter thumbnails from the directory listing.
        'filter' => true,
        // Filetypes which we restrict thumbnail operations to.
        'filetypes' => array("jpg", "gif", "png", "bmp"),
        // What pixel sizes to save the thumbnails as.
        'width' => 84,
        'height' => 84
    );


    /**
    * Resized prefix
    *
    * The prefix for resized files, something like .resized will do.  The
    * resized files will be named <prefix>_<width>x<height>_<original>
    * resized files are created when one changes the dimensions of an image
    * in the image manager selection dialog - the image is scaled when the
    * user clicks the ok button.
    */

    $Private['resized_prefix'] = '.resized';

    // -------------------------------------------------------------------------

    /**
    * Resized Directory
    *
    * Resized images may also be stored in a directory, except in safe mode.
    */

    $Private['resized_dir'] = '';

    /* Maximum upload file size

      Possible values: number, "max"

      number - maximum size in Kilobytes.

      "max"  - the maximum allowed by the server (the value is retrieved from the server configuration).
    */
    $Private['max_filesize_kb_image'] = 200;

    $Private['max_filesize_kb_link'] = 5000;

    /* Maximum upload folder size in Megabytes. Use 0 to disable limit */
    $Private['max_foldersize_mb'] = 0;

    /*
    Allowed extensions that can be shown and allowed to upload.
    Available icons are for "doc,fla,gif,gz,html,jpg,js,mov,pdf,php,png,ppt,rar,txt,xls,zip"
    -Changed by AFRU.
    */

    $Private['allowed_image_extensions'] = array("jpg","gif","png","bmp");
    $Private['allowed_link_extensions'] = array("jpg","gif","js","php","pdf","zip","txt","psd","png","html","swf","xml","xls","doc");


    /*
      Image Editor temporary filename prefix.
    */
    $Private['tmp_prefix'] = '.editor_';


    // Config variables are finished, this returns our data to the caller.
    if ($getprivates) {
        return $Public+$Private;
    }

    return $Public;
}
?>
