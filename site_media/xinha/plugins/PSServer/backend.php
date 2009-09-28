<?php
/**
 * File Operations API
 *
 * This file contains the new backend File Operations API used for Xinha File
 * Storage.  It will serve as the documentation for others wishing to implement
 * the backend in their own language, as well as the PHP implementation.  The
 * return data will come via the HTTP status in the case of an error, or JSON
 * data when call has succeeded.
 *
 * Some examples of the URLS associated with this API:
 * ** File Operations **
 * ?file&rename&filename=''&newname=''
 * ?file&copy&filename=''
 * ?file&delete&filename=''
 *
 * ** Directory Operations **
 * ?directory&listing
 * ?directory&create&dirname=''
 * ?directory&delete&dirname=''
 * ?directory&rename&dirname=''&newname=''
 *
 * ** Image Operations **
 * ?image&filename=''&[scale|rotate|convert]
 *
 * ** Upload **
 * ?upload&filedata=[binary|text]&filename=''&replace=[true|false]
 *
 * @author Douglas Mayle <douglas@openplans.org>
 * @version 1.0
 * @package PersistentStorage
 *
 */

/**
 * Config file
 */
require_once('config.inc.php');


// Strip slashes if MQGPC is on
set_magic_quotes_runtime(0);
if(get_magic_quotes_gpc())
{
  $to_clean = array(&$_GET, &$_POST, &$_REQUEST, &$_COOKIE);
  while(count($to_clean))
  {
    $cleaning =& $to_clean[array_pop($junk = array_keys($to_clean))];
    unset($to_clean[array_pop($junk = array_keys($to_clean))]);
    foreach(array_keys($cleaning) as $k)
    {
      if(is_array($cleaning[$k]))
      {
        $to_clean[] =& $cleaning[$k];
      }
      else
      {
        $cleaning[$k] = stripslashes($cleaning[$k]);
      }
    }
  }
}

// Set the return headers for a JSON response.
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
//header('Content-type: application/json');


/**#@+
 * Constants
 *
 * Since this is being used as part of a web interface, we'll set some rather
 * conservative limits to keep from overloading the user or the backend.
 */

/**
 * This is the maximum folder depth to present to the user
 */
define('MAX_DEPTH', 10);

/**
 * This is the maximum number of file entries per folder to show to the user,
 */
define('MAX_FILES_PER_FOLDER', 50);

/**
 * This array contains the default HTTP Response messages
 *
 */
$HTTP_ERRORS = array(
	'HTTP_SUCCESS_OK' => array('code' => 200, 'message' => 'OK'),
	'HTTP_SUCCESS_CREATED' => array('code' => 201, 'message' => 'Created'),
	'HTTP_SUCCESS_ACCEPTED' => array('code' => 202, 'message' => 'Accepted'),
	'HTTP_SUCCESS_NON_AUTHORITATIVE' => array('code' => 203, 'message' => 'Non-Authoritative Information'),
	'HTTP_SUCCESS_NO_CONTENT' => array('code' => 204, 'message' => 'No Content'),
	'HTTP_SUCCESS_RESET_CONTENT' => array('code' => 205, 'message' => 'Reset Content'),
	'HTTP_SUCCESS_PARTIAL_CONTENT' => array('code' => 206, 'message' => 'Partial Content'),

	'HTTP_REDIRECTION_MULTIPLE_CHOICES' => array('code' => 300, 'message' => 'Multiple Choices'),
	'HTTP_REDIRECTION_PERMANENT' => array('code' => 301, 'message' => 'Moved Permanently'),
	'HTTP_REDIRECTION_FOUND' => array('code' => 302, 'message' => 'Found'),
	'HTTP_REDIRECTION_SEE_OTHER' => array('code' => 303, 'message' => 'See Other'),
	'HTTP_REDIRECTION_NOT_MODIFIED' => array('code' => 304, 'message' => 'Not Modified'),
	'HTTP_REDIRECTION_USE_PROXY' => array('code' => 305, 'message' => 'Use Proxy'),
	'HTTP_REDIRECTION_UNUSED' => array('code' => 306, 'message' => '(Unused)'),
	'HTTP_REDIRECTION_TEMPORARY' => array('code' => 307, 'message' => 'Temporary Redirect'),

	'HTTP_CLIENT_BAD_REQUEST' => array('code' => 400, 'message' => 'Bad Request'),
	'HTTP_CLIENT_UNAUTHORIZED' => array('code' => 401, 'message' => 'Unauthorized'),
	'HTTP_CLIENT_PAYMENT_REQUIRED' => array('code' => 402, 'message' => 'Payment Required'),
	'HTTP_CLIENT_FORBIDDEN' => array('code' => 403, 'message' => 'Forbidden'),
	'HTTP_CLIENT_NOT_FOUND' => array('code' => 404, 'message' => 'Not Found'),
	'HTTP_CLIENT_METHOD_NOT_ALLOWED' => array('code' => 405, 'message' => 'Method Not Allowed'),
	'HTTP_CLIENT_NOT_ACCEPTABLE' => array('code' => 406, 'message' => 'Not Acceptable'),
	'HTTP_CLIENT_PROXY_AUTH_REQUIRED' => array('code' => 407, 'message' => 'Proxy Authentication Required'),
	'HTTP_CLIENT_REQUEST_TIMEOUT' => array('code' => 408, 'message' => 'Request Timeout'),
	'HTTP_CLIENT_CONFLICT' => array('code' => 409, 'message' => 'Conflict'),
	'HTTP_CLIENT_GONE' => array('code' => 410, 'message' => 'Gone'),
	'HTTP_CLIENT_LENGTH_REQUIRED' => array('code' => 411, 'message' => 'Length Required'),
	'HTTP_CLIENT_PRECONDITION_FAILED' => array('code' => 412, 'message' => 'Precondition Failed'),
	'HTTP_CLIENT_REQUEST_TOO_LARGE' => array('code' => 413, 'message' => 'Request Entity Too Large'),
	'HTTP_CLIENT_REQUEST_URI_TOO_LARGE' => array('code' => 414, 'message' => 'Request-URI Too Long'),
	'HTTP_CLIENT_UNSUPPORTED_MEDIA_TYPE' => array('code' => 415, 'message' => 'Unsupported Media Type'),
	'HTTP_CLIENT_REQUESTED_RANGE_NOT_POSSIBLE' => array('code' => 416, 'message' => 'Requested Range Not Satisfiable'),
	'HTTP_CLIENT_EXPECTATION_FAILED' => array('code' => 417, 'message' => 'Expectation Failed'),

	'HTTP_SERVER_INTERNAL' => array('code' => 500, 'message' => 'Internal Server Error'),
	'HTTP_SERVER_NOT_IMPLEMENTED' => array('code' => 501, 'message' => 'Not Implemented'),
	'HTTP_SERVER_BAD_GATEWAY' => array('code' => 502, 'message' => 'Bad Gateway'),
	'HTTP_SERVER_SERVICE_UNAVAILABLE' => array('code' => 503, 'message' => 'Service Unavailable'),
	'HTTP_SERVER_GATEWAY_TIMEOUT' => array('code' => 504, 'message' => 'Gateway Timeout'),
	'HTTP_SERVER_UNSUPPORTED_VERSION' => array('code' => 505, 'message' => 'HTTP Version not supported')
    );

/**
 * This is a regular expression used to detect reserved or dangerous filenames.
 * Most NTFS special filenames begin with a dollar sign ('$'), and most Unix
 * special filenames begin with a period (.), so we'll keep them out of this
 * list and just prevent those two characters in the first position.  The rest
 * of the special filenames are included below.
 */
define('RESERVED_FILE_NAMES', 'pagefile\.sys|a\.out|core');
/**
 * This is a regular expression used to detect invalid file names.  It's more
 * strict than necessary, to be valid multi-platform, but not posix-strict
 * because we want to allow unicode filenames.  We do, however, allow path
 * seperators in the filename because the file could exist in a subdirectory.
 */
define('INVALID_FILE_NAME','^[.$]|^(' . RESERVED_FILE_NAMES . ')$|[?%*:|"<>]');
/**#@-*/

function main($arguments) {
    $config = get_config(true);

    // Trigger authentication if it's configured.
    if ($config['capabilities']['user_storage'] && empty($_SERVER['PHP_AUTH_USER'])) {
        header('WWW-Authenticate: Basic realm="Xinha Persistent Storage"');
        header('HTTP/1.0 401 Unauthorized');
        echo "You must login in order to use Persistent Storage";
        exit;
    }
    if (!input_valid($arguments, $config['capabilities'])) {
        http_error_exit();
    }
    if (!method_valid($arguments)) {
        http_error_exit('HTTP_CLIENT_METHOD_NOT_ALLOWED');
    }
    if (!dispatch($arguments)) {
        http_error_exit();
    }
    exit();
}

main($_REQUEST + $_FILES);
// ************************************************************
// ************************************************************
//                       Helper Functions               
// ************************************************************
// ************************************************************

/**
 * Take the call and properly dispatch it to the methods below.  This method
 * assumes valid input.
 */
function dispatch($arguments) {
    if (array_key_exists('file', $arguments)) {
        if (array_key_exists('rename', $arguments)) {
            if (!file_directory_rename($arguments['filename'], $arguments['newname'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            return true;
        }
        if (array_key_exists('copy', $arguments)) {
            if (!$newentry = file_copy($arguments['filename'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            echo json_encode($newentry);
            return true;
        }
        if (array_key_exists('delete', $arguments)) {
            if (!file_delete($arguments['filename'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            return true;
        }
    }
    if (array_key_exists('directory', $arguments)) {
        if (array_key_exists('listing', $arguments)) {
            echo json_encode(directory_listing());
            return true;
        }
        if (array_key_exists('create', $arguments)) {
            if (!directory_create($arguments['dirname'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            return true;
        }
        if (array_key_exists('delete', $arguments)) {
            if (!directory_delete($arguments['dirname'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            return true;
        }
        if (array_key_exists('rename', $arguments)) {
            if (!file_directory_rename($arguments['dirname'], $arguments['newname'], working_directory())) {
                http_error_exit('HTTP_CLIENT_FORBIDDEN');
            }
            return true;
        }
    }
    if (array_key_exists('image', $arguments)) {
    }
    if (array_key_exists('upload', $arguments)) {
        store_uploaded_file($arguments['filename'], $arguments['filedata'], working_directory());
        return true;
    }

    return false;
}

/**
 * Validation of the HTTP Method.  For operations that make changes we require
 * POST.  To err on the side of safety, we'll only allow GET for known safe
 * operations.  This way, if the API is extended, and the method is not
 * updated, we will not accidentally expose non-idempotent methods to GET.
 * This method can only correctly validate the operation if the input is
 * already known to be valid.
 *
 * @param array $arguments The arguments array received by the page.
 * @return boolean Whether or not the HTTP method is correct for the given input.
 */
function method_valid($arguments) {
    // We assume that the only
    $method = $_SERVER['REQUEST_METHOD'];

    if ($method == 'GET') {
      if (array_key_exists('directory', $arguments) && array_key_exists('listing', $arguments)) {
          return true;
      }

      return false;
    }

    if ($method == 'POST') {
        return true;
    }
    return false;
}

/**
 * Validation of the user input.  We'll verify what we receive from the user,
 * and send an error in the case of malformed input.
 *
 * Some examples of the URLS associated with this API:
 * ** File Operations **
 * ?file&delete&filename=''
 * ?file&copy&filename=''
 * ?file&rename&filename=''&newname=''
 *
 * ** Directory Operations **
 * ?directory&listing
 * ?directory&create&dirname=''
 * ?directory&delete&dirname=''
 * ?directory&rename&dirname=''&newname=''
 *
 * ** Image Operations **
 * ?image&filename=''&[scale|rotate|convert]
 *
 * ** Upload **
 * ?upload&filedata=[binary|text]&filename=''&replace=[true|false]
 *
 * @param array $arguments The arguments array received by the page.
 * @param array $capabilities The capabilities config array used to limit operations.
 * @return boolean Whether or not the input received is valid.
 */
function input_valid($arguments, $capabilities) {
    // This is going to be really ugly code because it's basically a DFA for
    // parsing arguments.  To make things a little clearer, I'll put a
    // pseudo-BNF for each block to show the decision structure.
    //
    // file[empty] filename[valid] (delete[empty] | copy[empty] | (rename[empty] newname[valid]))
    if ($capabilities['file_operations'] &&
        array_key_exists('file', $arguments) &&
        empty($arguments['file']) &&
        array_key_exists('filename', $arguments) &&
        !ereg(INVALID_FILE_NAME, $arguments['filename'])) {

        if (array_key_exists('delete', $arguments) &&
            empty($arguments['delete']) &&
            3 == count($arguments)) {

            return true;
        }

        if (array_key_exists('copy', $arguments) &&
            empty($arguments['copy']) &&
            3 == count($arguments)) {

            return true;
        }

        if (array_key_exists('rename', $arguments) &&
            empty($arguments['rename']) &&
            4 == count($arguments)) {

            if (array_key_exists('newname', $arguments) &&
                !ereg(INVALID_FILE_NAME, $arguments['newname'])) {

                return true;
            }
        }

        return false;
    } elseif (array_key_exists('file', $arguments)) {
        // This isn't necessary because we'll fall through to false, but I'd
        // rather return earlier than later.
        return false;
    }

    // directory[empty] (listing[empty] | (dirname[valid] (create[empty] | delete[empty] | (rename[empty] newname[valid]))))
    if ($capabilities['directory_operations'] &&
        array_key_exists('directory', $arguments) &&
        empty($arguments['directory'])) {

        if (array_key_exists('listing', $arguments) &&
            empty($arguments['listing']) &&
            2 == count($arguments)) {

            return true;
        }

        if (array_key_exists('dirname', $arguments) &&
            !ereg(INVALID_FILE_NAME, $arguments['dirname'])) {

            if (array_key_exists('create', $arguments) &&
                empty($arguments['create']) &&
                3 == count($arguments)) {

                return true;
            }

            if (array_key_exists('delete', $arguments) &&
                empty($arguments['delete']) &&
                3 == count($arguments)) {

                return true;
            }

            if (array_key_exists('rename', $arguments) &&
                empty($arguments['rename']) &&
                4 == count($arguments)) {

                if (array_key_exists('newname', $arguments) &&
                    !ereg(INVALID_FILE_NAME, $arguments['newname'])) {

                    return true;
                }
            }
        }

        return false;
    } elseif (array_key_exists('directory', $arguments)) {
        // This isn't necessary because we'll fall through to false, but I'd
        // rather return earlier than later.
        return false;
    }

    // image[empty] filename[valid] ((scale[empty] dimensions[valid]) | (rotate[empty] angle[valid]) | (convert[empty] imagetype[valid]))
    if ($capabilities['image_operations'] &&
        array_key_exists('image', $arguments) &&
        empty($arguments['image']) &&
        array_key_exists('filename', $arguments) &&
        !ereg(INVALID_FILE_NAME, $arguments['filename']) &&
        4 == count($arguments)) {

        if (array_key_exists('scale', $arguments) &&
            empty($arguments['scale']) &&
            !ereg(INVALID_FILE_NAME, $arguments['dimensions'])) {
            // TODO: FIX REGEX
            http_error_exit();

            return true;
        }

        if (array_key_exists('rotate', $arguments) &&
            empty($arguments['rotate']) &&
            !ereg(INVALID_FILE_NAME, $arguments['angle'])) {
            // TODO: FIX REGEX
            http_error_exit();

            return true;
        }

        if (array_key_exists('convert', $arguments) &&
            empty($arguments['convert']) &&
            !ereg(INVALID_FILE_NAME, $arguments['imagetype'])) {
            // TODO: FIX REGEX
            http_error_exit();

            return true;
        }

        return false;
    } elseif (array_key_exists('image', $arguments)) {
        // This isn't necessary because we'll fall through to false, but I'd
        // rather return earlier than later.
        return false;
    }

    // upload[empty] filedata[binary|text] replace[true|false] filename[valid]?
    if ($capabilities['upload_operations'] &&
        array_key_exists('upload', $arguments) &&
        empty($arguments['upload']) &&
        array_key_exists('filedata', $arguments) &&
        !empty($arguments['filedata']) &&
        array_key_exists('replace', $arguments) &&
        ereg('true|false', $arguments['replace'])) {

        if (4 == count($arguments) &&
            array_key_exists('filename', $arguments) &&
            !ereg(INVALID_FILE_NAME, $arguments['filename'])) {

            return true;
        }

        if (3 == count($arguments)) {

            return true;
        }

        return false;
    } elseif (array_key_exists('upload', $arguments)) {
        // This isn't necessary because we'll fall through to false, but I'd
        // rather return earlier than later.
        return false;
    }


    return false;
}

/**
 * HTTP level error handling. 
 * @param integer $code The HTTP error code to return to the client.  This defaults to 400.
 * @param string $message Error message to send to the client.  This defaults to the standard HTTP error messages.
 */
function http_error_exit($error = 'HTTP_CLIENT_BAD_REQUEST', $message='') {
    global $HTTP_ERRORS;
    $message = !empty($message) ? $message : "HTTP/1.0 {$HTTP_ERRORS[$error]['code']} {$HTTP_ERRORS[$error]['message']}";
    header($message);
    exit($message);
}

/**
 * Process the config and return the absolute directory we should be working with,
 * @return string contains the path of the directory all file operations are limited to.
 */
function working_directory() {
    $config = get_config(true);
    return realpath(getcwd() . DIRECTORY_SEPARATOR . $config['storage_dir'] . DIRECTORY_SEPARATOR);
}

/**
 * Check to see if the supplied filename is inside
 */
function directory_contains($container_directory, $checkfile) {

    // Get the canonical directory and canonical filename.  We add a directory
    // seperator to prevent the user from sidestepping into a sibling directory
    // that starts with the same prefix. (e.g. from /home/john to
    // /home/johnson)
    $container_directory = realpath($container_directory) + DIRECTORY_SEPARATOR;
    $checkfile = realpath($checkfile);

    // Now that we have the canonical versions, we can do a string comparison
    // to see if checkfile is inside of container_directory.
    if (strlen($checkfile) <= strlen($container_directory)) {
        // We don't consider the directory to be inside of itself.  This
        // prevents users from trying to perform operations on the container
        // directory itself.
        return false;
    }

    // PHP equivalent of string.startswith()
    return substr($checkfile, 0, strlen($container_directory)) == $container_directory;
}

/**#@+
 *                             Directory Operations
 * {@internal *****************************************************************
 * **************************************************************************}}
 */

/**
 * Return a directory listing as a PHP array.
 * @param string $directory The directory to return a listing of.
 * @param integer $depth The private argument used to limit recursion depth.
 * @return array representing the directory structure. 
 */

function directory_listing($directory='', $depth=1) {
    // We return an empty array if the directory is empty
    $result = array('$type'=>'folder');

    // We won't recurse below MAX_DEPTH.
    if ($depth > MAX_DEPTH) {
        return $result;
    }

    $path = empty($directory) ? working_directory() : $directory;

    // We'll open the directory to check each of the entries
    if ($dir = opendir($path)) {

        // We'll keep track of how many file we process.
        $count = 0;

        // For each entry in the file
        while (($file = readdir($dir)) !== false) {

            // Limit the number of files we process in this folder
            $count += 1;
            if ($count > MAX_FILES_PER_FOLDER) {
                return $result;
            }

            // Ignore hidden files (this includes special files '.' and '..')
            if (strlen($file) && ($file[0] == '.')) {
                continue;
            }

            $filepath = $path . DIRECTORY_SEPARATOR . $file;

            if (filetype($filepath) == 'dir') {
                // We'll recurse and add those results
                $result[$file] = directory_listing($filepath, $depth + 1);
            } else {
                // We'll check to see if we can read any image information from
                // the file.  If so, we know it's an image, and we can return
                // it's metadata.
                $imageinfo = @getimagesize($filepath);
                if ($imageinfo) {

                  $result[$file] = array('$type'=>'image','metadata'=>array(
                                  'width'=>$imageinfo[0],
                                  'height'=>$imageinfo[1],
                                  'mimetype'=>$imageinfo['mime']
                              ));

                } elseif ($extension = strrpos($file, '.')) {
                     $extension = substr($file, $extension);
                     if (($extension == '.htm') || ($extension == '.html')) {
                         $result[$file] = array('$type'=>'html');
                     } else {
                         $result[$file] = array('$type'=>'text');
                     }
                } else {
                    $result[$file] = array('$type'=>'document');
                }
            }
        }
        
        closedir($dir);
    }
    return $result;
}

/**
 * Create a directory, limiting operations to the chroot directory.
 * @param string $dirname The path to the directory, relative to $chroot.
 * @param string $chroot Only directories inside this directory or its subdirectories can be affected.
 * @return boolean Returns TRUE if successful, and FALSE otherwise.
 */
function directory_create($dirname, $chroot) {
    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // We have to take the dirname of the parent directory first, since
    // realpath just returns false if the directory doesn't already exist on
    // the filesystem.
    $createparent = realpath(dirname($chroot . DIRECTORY_SEPARATOR . $dirname));
    $createsub = basename($chroot . DIRECTORY_SEPARATOR . $dirname);

    // The bailout rules for directories that don't exist are complicated
    // because of having to work around realpath.  If the parent directory is
    // the same as the chroot, it won't be contained.  For this case, we'll
    // check to see if the chroot and the parent are the same and allow it only
    // if the sub portion of dirname is not-empty.
    if (!directory_contains($chroot, $createparent) &&
        !(($chroot == $createparent) && !empty($createsub))) {
        return false;
    }

    return @mkdir($createparent . DIRECTORY_SEPARATOR . $createsub);
}

/**
 * Delete a directory, limiting operations to the chroot directory.
 * @param string $dirname The path to the directory, relative to $chroot.
 * @param string $chroot Only directories inside this directory or its subdirectories can be affected.
 * @return boolean Returns TRUE if successful, and FALSE otherwise.
 */
function directory_delete($dirname, $chroot) {
    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // $dirname is relative to $chroot.
    $dirname = realpath($chroot . DIRECTORY_SEPARATOR . $dirname);

    // Limit directory operations to the supplied directory.
    if (!directory_contains($chroot, $dirname)) {
        return false;
    }

    return @rmdir($dirname);
}


/**#@-*/
/**#@+
 *                               File Operations
 * {@internal *****************************************************************
 * **************************************************************************}}
 */

/**
 * Rename a file or directory, limiting operations to the chroot directory.
 * @param string $filename The path to the file or directory, relative to $chroot.
 * @param string $renameto The path to the renamed file or directory, relative to $chroot.
 * @param string $chroot Only files and directories inside this directory or its subdirectories can be affected.
 * @return boolean Returns TRUE if successful, and FALSE otherwise.
 */
function file_directory_rename($filename, $renameto, $chroot) {
    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // $filename is relative to $chroot.
    $filename = realpath($chroot . DIRECTORY_SEPARATOR . $filename);

    // We have to take the dirname of the renamed file or directory first,
    // since realpath just returns false if the file or direcotry doesn't
    // already exist on the filesystem.
    $renameparent = realpath(dirname($chroot . DIRECTORY_SEPARATOR . $renameto));
    $renamefile = basename($chroot . DIRECTORY_SEPARATOR . $renameto);

    // Limit file operations to the supplied directory.
    if (!directory_contains($chroot, $filename)) {
        return false;
    }

    // The bailout rules for the renamed file or directory are more complicated
    // because of having to work around realpath.  If the renamed parent
    // directory is the same as the chroot, it won't be contained.  For this
    // case, we'll check to see if they're the same and allow it only if the
    // file portion of renameto is not-empty.
    if (!directory_contains($chroot, $renameparent) &&
        !(($chroot == $renameparent) && !empty($renamefile))) {
        return false;
    }

    return @rename($filename, $renameparent . DIRECTORY_SEPARATOR . $renamefile);
}


/**
 * Copy a file, limiting operations to the chroot directory.
 * @param string $filename The path to the file, relative to $chroot.
 * @param string $chroot Only files inside this directory or its subdirectories can be affected.
 * @return boolean Returns TRUE if successful, and FALSE otherwise.
 */
function file_copy($filename, $chroot) {
    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // $filename is relative to $chroot.
    $filename = realpath($chroot . DIRECTORY_SEPARATOR . $filename);

    // Limit file operations to the supplied directory.
    if (!directory_contains($chroot, $filename)) {
        return false;
    }

    // The PHP copy function blindly copies over existing files.  We don't wish
    // this to happen, so we have to perform the copy a bit differently.  If we
    // do a check to make sure the file exists, there's always the chance of a
    // race condition where someone else creates the file in between the check
    // and the copy.  The only safe way to ensure we don't overwrite an
    // existing file is to call fopen in create-only mode (mode 'x').  If it
    // succeeds, the file did not exist before, and we've successfully created
    // it, meaning we own the file.  After that, we can safely copy over our
    // own file.
    for ($count=1; $count<MAX_FILES_PER_FOLDER; ++$count) {
        if (strpos(basename($filename), '.')) {
            $extpos = strrpos($filename, '.');
            $copyname = substr($filename, 0, $extpos) . '_' . $count . substr($filename, $extpos);
        } else {
            // There's no extension, we we'll just add our copy count.
            $copyname = $filename . '_' . $count;
        }
        if ($file = @fopen($copyname, 'x')) {
            // We've successfully created a file, so it's ours.  We'll close
            // our handle.
            if (!@fclose($file)) {
                // There was some problem with our file handle.
                return false;
            }

            // Now we copy over the file we created.
            if (!@copy($filename, $copyname)) {
                // The copy failed, even though we own the file, so we'll clean
                // up by removing the file and report failure.
                file_delete($filename, $chroot);
                return false;
            }

            return array(basename($copyname)=>array('$type'=>'image'));
        }
    }

    return false;
}

/**
 * Delete a file, limiting operations to the chroot directory.
 * @param string $filename The path to the file, relative to $chroot.
 * @param string $chroot Only files inside this directory or its subdirectories can be affected.
 * @return boolean Returns TRUE if successful, and FALSE otherwise.
 */
function file_delete($filename, $chroot) {
    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // $filename is relative to $chroot.
    $filename = realpath($chroot . DIRECTORY_SEPARATOR . $filename);

    // Limit file operations to the supplied directory.
    if (!directory_contains($chroot, $filename)) {
        return false;
    }

    return @unlink($filename);
}
/**#@-*/
/**#@+
 *                              Upload Operations
 * {@internal *****************************************************************
 * **************************************************************************}}
 */

function store_uploaded_file($filename, $filedata, $chroot) {

    // If chroot is empty, then we will not perform the operation.
    if (empty($chroot)) {
        return false;
    }

    // If the filename is empty, it was possibly supplied as part of the
    // upload.
    $filename = empty($filename) ? $filedata['name'] : $filename;

    // We have to take the dirname of the parent directory first, since
    // realpath just returns false if the directory doesn't already exist on
    // the filesystem.
    $uploadparent = realpath(dirname($chroot . DIRECTORY_SEPARATOR . $filename));
    $uploadfile = basename($chroot . DIRECTORY_SEPARATOR . $filename);

    // The bailout rules for directories that don't exist are complicated
    // because of having to work around realpath.  If the parent directory is
    // the same as the chroot, it won't be contained.  For this case, we'll
    // check to see if the chroot and the parent are the same and allow it only
    // if the sub portion of dirname is not-empty.
    if (!directory_contains($chroot, $uploadparent) &&
        !(($chroot == $uploadparent) && !empty($uploadfile))) {
        return false;
    }
 
    $target_path = $uploadparent . DIRECTORY_SEPARATOR . $uploadfile;

    if (is_array($filedata)) {
        // We've received the file as an upload, so it's been saved to a temp
        // directory.  We'll move it to where it belongs.
     
        if(move_uploaded_file($filedata['tmp_name'], $target_path)) {
            return true;
        }
    } elseif ($file = @fopen($target_path, 'w')) {
        // We've received the file as data.  We'll create/open the file and
        // save the data.
        @fwrite($file, $filedata);
        @fclose($file);
        return true;
    }
 
    return false;
}

/**#@-*/

?>
