<?php
/**
 * ExtendedFileManager, list images, directories, and thumbnails.
 * Authors: Wei Zhuo, Afru, Krzysztof Kotowicz, Raimund Meyer
 * Version: Updated on 08-01-2005 by Afru
 * Version: Updated on 04-07-2006 by Krzysztof Kotowicz
 * Version: Updated on 29-10-2006 by Raimund Meyer
 * Package: ExtendedFileManager (EFM 1.1.3)
 * http://www.afrusoft.com/htmlarea
 */

/**
 * We use classes from ImageManager to avoid code duplication
 */
require_once '../ImageManager/Classes/Files.php';

/**
 * ExtendedFileManager Class.
 * @author Wei Zhuo, Afru, Krzysztof Kotowicz, Raimund Meyer
 * @version $Id: ExtendedFileManager.php 1171 2009-03-19 22:06:09Z ray $
 */
class ExtendedFileManager 
{
	/**
	 * Configuration array.
	 */
	var $config;

	/**
	 * Array of directory information.
	 */
	var $dirs;
	
    /**
     * Manager mode - image | link
     */
	var $mode;

	/**
	 * Constructor. Create a new Image Manager instance.
	 * @param array $config configuration array, see config.inc.php
	 */
	function ExtendedFileManager($config, $mode = null)
	{
		$this->config = $config;
		
		$this->mode = empty($mode) ? (empty($config['insert_mode']) ? 'image' : $config['insert_mode']): $mode;
	}

	/**
	 * Get the base directory.
	 * @return string base dir, see config.inc.php
	 */
	function getImagesDir()
	{
		if ($this->mode == 'link' && isset($this->config['files_dir']))
			Return $this->config['files_dir'];
		else Return $this->config['images_dir'];
	}

	/**
	 * Get the base URL.
	 * @return string base url, see config.inc.php
	 */
	function getImagesURL()
	{
		if ($this->mode == 'link' && isset($this->config['files_url']))
				Return $this->config['files_url'];
		else Return $this->config['images_url'];
	}

	function isValidBase()
	{
		return is_dir($this->getImagesDir());
	}

	/**
	 * Get the tmp file prefix.
     * @return string tmp file prefix.
	 */
	function getTmpPrefix() 
	{
		Return $this->config['tmp_prefix'];
	}

	/**
	 * Get the sub directories in the base dir.
	 * Each array element contain
	 * the relative path (relative to the base dir) as key and the 
	 * full path as value.
	 * @return array of sub directries
	 * <code>array('path name' => 'full directory path', ...)</code>
	 */
	function getDirs() 
	{
		if(is_null($this->dirs))
		{
			$dirs = $this->_dirs($this->getImagesDir(),'/');
			ksort($dirs);
			$this->dirs = $dirs;
		}
		return $this->dirs;
	}

	/**
	 * Recursively travese the directories to get a list
	 * of accessable directories.
	 * @param string $base the full path to the current directory
	 * @param string $path the relative path name
	 * @return array of accessiable sub-directories
	 * <code>array('path name' => 'full directory path', ...)</code>
	 */
	function _dirs($base, $path) 
	{
		$base = Files::fixPath($base);
		$dirs = array();

		if($this->isValidBase() == false)
			return $dirs;

		$d = @dir($base);
		
		while (false !== ($entry = $d->read())) 
		{
			//If it is a directory, and it doesn't start with
			// a dot, and if is it not the thumbnail directory
			if(is_dir($base.$entry) 
				&& substr($entry,0,1) != '.'
				&& $this->isThumbDir($entry) == false) 
			{
				$relative = Files::fixPath($path.$entry);
				$fullpath = Files::fixPath($base.$entry);
				$dirs[$relative] = $fullpath;
				$dirs = array_merge($dirs, $this->_dirs($fullpath, $relative));
			}
		}
		$d->close();

		Return $dirs;
	}

	/**
	 * Get all the files and directories of a relative path.
	 * @param string $path relative path to be base path.
	 * @return array of file and path information.
	 * <code>array(0=>array('relative'=>'fullpath',...), 1=>array('filename'=>fileinfo array(),...)</code>
	 * fileinfo array: <code>array('url'=>'full url', 
	 *                       'relative'=>'relative to base', 
	 *                        'fullpath'=>'full file path', 
	 *                        'image'=>imageInfo array() false if not image,
	 *                        'stat' => filestat)</code>
	 */
	function getFiles($path) 
	{
		$files = array();
		$dirs = array();

        $valid_extensions = $this->mode == 'image' ? $this->config['allowed_image_extensions'] : $this->config['allowed_link_extensions'];

		if($this->isValidBase() == false)
			return array($files,$dirs);

		$path = Files::fixPath($path);
		$base = Files::fixPath($this->getImagesDir());
		$fullpath = Files::makePath($base,$path);


		$d = @dir($fullpath);
		
		while (false !== ($entry = $d->read())) 
		{
			//not a dot file or directory
			if(substr($entry,0,1) != '.')
			{
				if(is_dir($fullpath.$entry)
					&& $this->isThumbDir($entry) == false)
				{
					$relative = Files::fixPath($path.$entry);
					$full = Files::fixPath($fullpath.$entry);
					$count = $this->countFiles($full);
					$dirs[$relative] = array('fullpath'=>$full,'entry'=>$entry,'count'=>$count, 'stat'=>stat($fullpath.$entry));
				}

				else if(is_file($fullpath.$entry) && $this->isThumb($entry)==false && $this->isTmpFile($entry) == false) 
				{
					$afruext = strtolower(substr(strrchr($entry, "."), 1));

                    if(in_array($afruext,$valid_extensions))
					{

						$file['url'] = Files::makePath($this->config['base_url'],$path).$entry;
						$file['relative'] = $path.$entry;
						$file['fullpath'] = $fullpath.$entry;
						$img = $this->getImageInfo($fullpath.$entry);
						if(!is_array($img)) $img[0]=$img[1]=0;
						$file['image'] = $img;
						$file['stat'] = stat($fullpath.$entry);
						$file['ext'] = $afruext;
						$files[$entry] = $file;
					}

				}
			}
		}
		$d->close();
		ksort($dirs);
		ksort($files);
		
		Return array($dirs, $files);
	}	

	/**
	 * Count the number of files and directories in a given folder
	 * minus the thumbnail folders and thumbnails.
	 */
	function countFiles($path) 
	{
		$total = 0;

		if(is_dir($path)) 
		{
			$d = @dir($path);

			while (false !== ($entry = $d->read())) 
			{
				//echo $entry."<br>";
				if(substr($entry,0,1) != '.'
					&& $this->isThumbDir($entry) == false
					&& $this->isTmpFile($entry) == false
					&& $this->isThumb($entry) == false) 
				{
					$total++;
				}
			}
			$d->close();
		}
		return $total;
	}

	/**
	 * Get image size information.
	 * @param string $file the image file
	 * @return array of getImageSize information, 
	 *  false if the file is not an image.
	 */
	function getImageInfo($file) 
	{
		Return @getImageSize($file);
	}

	/**
	 * Check if the file contains the thumbnail prefix.
	 * @param string $file filename to be checked
	 * @return true if the file contains the thumbnail prefix, false otherwise.
	 */
	function isThumb($file) 
	{
		$len = strlen($this->config['thumbnail_prefix']);
		if(substr($file,0,$len)==$this->config['thumbnail_prefix'])
			Return true;
		else
			Return false;
	}

	/**
	 * Check if the given directory is a thumbnail directory.
	 * @param string $entry directory name
	 * @return true if it is a thumbnail directory, false otherwise
	 */
	function isThumbDir($entry) 
	{
		if($this->config['thumbnail_dir'] == false
			|| strlen(trim($this->config['thumbnail_dir'])) == 0)
			Return false;		
		else
			Return ($entry == $this->config['thumbnail_dir']);
	}

	/**
	 * Check if the given file is a tmp file.
	 * @param string $file file name
	 * @return boolean true if it is a tmp file, false otherwise
	 */
	function isTmpFile($file) 
	{
		$len = strlen($this->config['tmp_prefix']);
		if(substr($file,0,$len)==$this->config['tmp_prefix'])
			Return true;
		else
			Return false;	 	
	}

	/**
	 * For a given image file, get the respective thumbnail filename
	 * no file existence check is done.
	 * @param string $fullpathfile the full path to the image file
	 * @return string of the thumbnail file
	 */
	function getThumbName($fullpathfile) 
	{
		$path_parts = pathinfo($fullpathfile);
		
		$thumbnail = $this->config['thumbnail_prefix'].$path_parts['basename'];

		if($this->config['safe_mode'] == true
			|| strlen(trim($this->config['thumbnail_dir'])) == 0)
		{
			Return Files::makeFile($path_parts['dirname'],$thumbnail);
		}
		else
		{
			if(strlen(trim($this->config['thumbnail_dir'])) > 0)
			{
				$path = Files::makePath($path_parts['dirname'],$this->config['thumbnail_dir']);
				if(!is_dir($path))
					Files::createFolder($path);
				Return Files::makeFile($path,$thumbnail);
			}
			else //should this ever happen?
			{
				//error_log('ExtendedFileManager: Error in creating thumbnail name');
			}
		}
	}
	
	/**
	 * Similar to getThumbName, but returns the URL, base on the
	 * given base_url in config.inc.php
	 * @param string $relative the relative image file name, 
	 * relative to the base_dir path
	 * @return string the url of the thumbnail
	 */
	function getThumbURL($relative) 
	{
		$path_parts = pathinfo($relative);
		$thumbnail = $this->config['thumbnail_prefix'].$path_parts['basename'];
		if($path_parts['dirname']=='\\') $path_parts['dirname']='/';

		if($this->config['safe_mode'] == true
			|| strlen(trim($this->config['thumbnail_dir'])) == 0)
		{
			Return Files::makeFile($this->getImagesURL(),$thumbnail);
		}
		else
		{
			if(strlen(trim($this->config['thumbnail_dir'])) > 0)
			{
				$path = Files::makePath($path_parts['dirname'],$this->config['thumbnail_dir']);
				$url_path = Files::makePath($this->getImagesURL(), $path);
				Return Files::makeFile($url_path,$thumbnail);
			}
			else //should this ever happen?
			{
				//error_log('ExtendedFileManager: Error in creating thumbnail url');
			}

		}
	}

   /**
    * For a given image file, get the respective resized filename
    * no file existence check is done.
    * @param string $fullpathfile the full path to the image file
    * @param integer $width the intended width
    * @param integer $height the intended height
    * @param boolean $mkDir whether to attempt to make the resized_dir if it doesn't exist
    * @return string of the resized filename
    */
	function getResizedName($fullpathfile, $width, $height, $mkDir = TRUE)
	{
		$path_parts = pathinfo($fullpathfile);

		$thumbnail = $this->config['resized_prefix']."_{$width}x{$height}_{$path_parts['basename']}";

		if( strlen(trim($this->config['resized_dir'])) == 0 || $this->config['safe_mode'] == true )
		{
			Return Files::makeFile($path_parts['dirname'],$thumbnail);
		}
		else
		{
      $path = Files::makePath($path_parts['dirname'],$this->config['resized_dir']);
      if($mkDir && !is_dir($path))
        Files::createFolder($path);
      Return Files::makeFile($path,$thumbnail);
		}
	}

	/**
	 * Check if the given path is part of the subdirectories
	 * under the base_dir.
	 * @param string $path the relative path to be checked
	 * @return boolean true if the path exists, false otherwise
	 */
	function validRelativePath($path) 
	{
		$dirs = $this->getDirs();
		if($path == '/')
			Return true;
		//check the path given in the url against the 
		//list of paths in the system.
		for($i = 0; $i < count($dirs); $i++)
		{
			$key = key($dirs);
			//we found the path
			if($key == $path)
				Return true;
		
			next($dirs);
		}		
		Return false;
	}

	/**
	 * Process uploaded files, assumes the file is in 
	 * $_FILES['upload'] and $_POST['dir'] is set.
	 * The dir must be relative to the base_dir and exists.
	 * @return null
	 */
	function processUploads() 
	{
		if($this->isValidBase() == false)
			return;

		$relative = null;

		if(isset($_POST['dir'])) 
			$relative = rawurldecode($_POST['dir']);
		else
			return;

		//check for the file, and must have valid relative path
		if(isset($_FILES['upload']) && $this->validRelativePath($relative))
		{
			Return $this->_processFiles($relative, $_FILES['upload']);
		}
	}

	/**
	 * Process upload files. The file must be an 
	 * uploaded file. Any duplicate
	 * file will be renamed. See Files::copyFile for details
	 * on renaming.
	 * @param string $relative the relative path where the file
	 * should be copied to.
	 * @param array $file the uploaded file from $_FILES
	 * @return boolean true if the file was processed successfully, 
	 * false otherwise
	 */
	function _processFiles($relative, $file)
	{
		
		if($file['error']!=0)
		{
			Return false;
		}

		if(!is_uploaded_file($file['tmp_name']))
		{
			Files::delFile($file['tmp_name']);
			Return false;
		}

        $valid_extensions = $this->mode == 'image' ? $this->config['allowed_image_extensions'] : $this->config['allowed_link_extensions'];
        $max_size = $this->mode == 'image' ? $this->config['max_filesize_kb_image'] : $this->config['max_filesize_kb_link'];
		$afruext = strtolower(substr(strrchr($file['name'], "."), 1));

		if(!in_array($afruext, $valid_extensions))
		{
			Files::delFile($file['tmp_name']);
			Return 'Cannot upload $extension='.$afruext.'$ Files. Permission denied.';
		}

		if($file['size']>($max_size*1024))
		{
			Files::delFile($file['tmp_name']);
			Return 'Unble to upload file. Maximum file size [$max_size='.$max_size.'$ KB] exceeded.';
		}

		if(!empty($this->config['max_foldersize_mb']) &&  (Files::dirSize($this->getImagesDir()))+$file['size']> ($this->config['max_foldersize_mb']*1048576))
		{
			Files::delFile($file['tmp_name']);
			Return ("Cannot upload. Maximum folder size reached. Delete unwanted files and try again.");
		}

		//now copy the file
		$path = Files::makePath($this->getImagesDir(),$relative);
		$result = Files::copyFile($file['tmp_name'], $path, $file['name']);

		//no copy error
		if(!is_int($result))
		{
			Files::delFile($file['tmp_name']);
			Return 'File "$file='.$file['name'].'$" successfully uploaded.';
		}

		//delete tmp files.
		Files::delFile($file['tmp_name']);
		Return false;

	}


	function getDiskInfo()
	{
        if (empty($this->config['max_foldersize_mb']))
            return '';
            
		$tmpFreeSize=($this->config['max_foldersize_mb']*1048576)-Files::dirSize($this->getImagesDir());

		if(!is_numeric($tmpFreeSize) || $tmpFreeSize<0)	$tmpFreeSize=0;
        
		Return 'Total Size : $max_foldersize_mb='.$this->config['max_foldersize_mb'].'$ MB, Free Space: $free_space='.Files::formatSize($tmpFreeSize).'$';
	}



	/**
	 * Get the URL of the relative file.
	 * basically appends the relative file to the 
	 * base_url given in config.inc.php
	 * @param string $relative a file the relative to the base_dir
	 * @return string the URL of the relative file.
	 */
	function getFileURL($relative) 
	{
		Return Files::makeFile($this->getImagesURL(),$relative);
	}

	/**
	 * Get the fullpath to a relative file.
	 * @param string $relative the relative file.
	 * @return string the full path, .ie. the base_dir + relative.
	 */
	function getFullPath($relative) 
	{
		Return Files::makeFile($this->getImagesDir(),$relative);;
	}

	/**
	 * Get the default thumbnail.
	 * @return string default thumbnail, empty string if 
	 * the thumbnail doesn't exist.
	 */
	function getDefaultThumb() 
	{
		if(is_file($this->config['default_thumbnail']))
			Return $this->config['default_thumbnail'];
		else 
			Return '';
	}


	/**
	 * Checks image size. If the image size is less than default size
	 * returns the original size else returns default size to display thumbnail
	*/
	function checkImageSize($relative)
	{
		$fullpath = Files::makeFile($this->getImagesDir(),$relative);

		$afruext = strtolower(substr(strrchr($relative, "."), 1));
		
		if(!in_array($afruext,$this->config['thumbnail_extensions']))
		{
			$imgInfo=array(0,0);
			Return $imgInfo;
		}
		else
		{
			$imgInfo = @getImageSize($fullpath);
			//not an image
			if(!is_array($imgInfo))
			{
				$imgInfo=array(0,0);
				Return $imgInfo;
			}
			else
			{
				if($imgInfo[0] > $this->config['thumbnail_width'])
				$imgInfo[0] = $this->config['thumbnail_width'];

				if($imgInfo[1] > $this->config['thumbnail_height'])
				$imgInfo[1] = $this->config['thumbnail_height'];

				Return $imgInfo;
			}
		}

	}


	/**
	 * Get the thumbnail url to be displayed. 
	 * If the thumbnail exists, and it is up-to-date
	 * the thumbnail url will be returns. If the 
	 * file is not an image, a default image will be returned.
	 * If it is an image file, and no thumbnail exists or 
	 * the thumbnail is out-of-date (i.e. the thumbnail 
	 * modified time is less than the original file)
	 * then a thumbs.php?img=filename.jpg is returned.
	 * The thumbs.php url will generate a new thumbnail
	 * on the fly. If the image is less than the dimensions
	 * of the thumbnails, the image will be display instead.
	 * @param string $relative the relative image file.
	 * @return string the url of the thumbnail, be it
	 * actually thumbnail or a script to generate the
	 * thumbnail on the fly.
	 */
	function getThumbnail($relative) 
	{
		global $IMConfig;
		
		$fullpath = Files::makeFile($this->getImagesDir(),$relative);

		//not a file???
		if(!is_file($fullpath))
			Return $this->getDefaultThumb();

		$afruext = strtolower(substr(strrchr($relative, "."), 1));
		
		if(!in_array($afruext,$this->config['thumbnail_extensions']))
		{
			if(is_file('icons/'.$afruext.'.gif')) 
				Return('icons/'.$afruext.'.gif');
			else
				Return $this->getDefaultThumb();
		}

		$imgInfo = @getImageSize($fullpath);

		//not an image
		if(!is_array($imgInfo))
			Return $this->getDefaultThumb();


		//Returning original image as thumbnail without Image Library by Afru
		if(!$this->config['img_library']) Return $this->getFileURL($relative);


		//the original image is smaller than thumbnails,
		//so just return the url to the original image.
		if ($imgInfo[0] <= $this->config['thumbnail_width']
		 && $imgInfo[1] <= $this->config['thumbnail_height'])
			Return $this->getFileURL($relative);

		$thumbnail = $this->getThumbName($fullpath);
		
		//check for thumbnails, if exists and
		// it is up-to-date, return the thumbnail url
		if(is_file($thumbnail))
		{
			if(filemtime($thumbnail) >= filemtime($fullpath))
				Return $this->getThumbURL($relative);
		}

		//well, no thumbnail was found, so ask the thumbs.php
		//to generate the thumbnail on the fly.
		Return $IMConfig['backend_url'] . '__function=thumbs&img='.rawurlencode($relative)."&mode=$this->mode";
	}

	/**
	 * Delete and specified files.
	 * @return boolean true if delete, false otherwise
	 */
	function deleteFiles() 
	{
		if(isset($_GET['delf']))
			return $this->_delFile(rawurldecode($_GET['delf']));
        return false;
	}

	/**
	 * Delete and specified directories.
	 * @return boolean true if delete, false otherwise
	 */
	function deleteDirs() 
	{
		 if(isset($_GET['deld']))
			return $this->_delDir(rawurldecode($_GET['deld']));		
		 else
			 Return false;
	}

	/**
	 * Delete the relative file, and any thumbnails.
	 * @param string $relative the relative file.
	 * @return boolean true if deleted, false otherwise.
	 */
	function _delFile($relative) 
	{
		$fullpath = Files::makeFile($this->getImagesDir(),$relative);
	
		$afruext = strtolower(substr(strrchr($relative, "."), 1));

        $valid_extensions = $this->mode == 'image' ? $this->config['allowed_image_extensions'] : $this->config['allowed_link_extensions'];

		if(!in_array($afruext,$valid_extensions))
		{
			return false;
		}

		//check that the file is an image
		if(is_array($this->getImageInfo($fullpath)))
		{
			$thumbnail = $this->getThumbName($fullpath);
			Files::delFile($thumbnail);
		}

		Return Files::delFile($fullpath);
	}

	/**
	 * Delete directories recursively.
	 * @param string $relative the relative path to be deleted.
	 * @return boolean true if deleted, false otherwise.
	 */
	function _delDir($relative) 
	{
		$fullpath = Files::makePath($this->getImagesDir(),$relative);
	//	if($this->countFiles($fullpath) <= 0)
			return Files::delFolder($fullpath,true); //delete recursively.
		//else
			//Return false;
	}

	/**
	 * Create new directories.
	 * If in safe_mode, nothing happens.
	 * @return boolean true if created, false otherwise.
	 */
	function processNewDir() 
	{
		if($this->config['safe_mode'] == true)
			Return false;

		if(isset($_GET['newDir']) && isset($_GET['dir']))
		{
			$newDir = rawurldecode($_GET['newDir']);
			$dir = rawurldecode($_GET['dir']);
			$path = Files::makePath($this->getImagesDir(),$dir);
			$fullpath = Files::makePath($path, Files::escape($newDir));
			if(is_dir($fullpath))
				Return false;

			Return Files::createFolder($fullpath);
		}
	}

	/**
	 * Renames files if certain GET variables are set
	 * @return bool
	 */
	function processRenames()
	{
		if(!empty($_GET['rename']) && !empty($_GET['renameTo']))
		{
			// new file name (without path and extension)
			$newName = Files::escape(rawurldecode($_GET['renameTo']));
			$newName = str_replace('.', '', $newName);

			// path to file (from base images directory)
			$oldName = rawurldecode($_GET['rename']);

			// strip parent dir ("..") to avoid escaping from base directiory
			$oldName = preg_replace('#\.\.#', '', $oldName);

			if (is_dir($oldPath = Files::makeFile($this->getImagesDir(), $_GET['dir'].$oldName)))
			{
				$newPath = Files::makeFile($this->getImagesDir(), $_GET['dir'].$newName);
				return Files::rename($oldPath,$newPath);
			}
			else 
			{
				// path to old file
				$oldPath = Files::makeFile($this->getImagesDir(), $oldName);
	
				$ret = Files::renameFile($oldPath, $newName);
				if ($ret === true) {
					// delete old thumbnail
					Files::delFile($this->getThumbname($oldPath));
				}
			}
			return $ret;
		}
		
		return null;
	}

	function processPaste()
	{
		switch ($_GET['paste'])
		{
			case 'copyFile':
				$src = Files::makeFile($this->getImagesDir(), $_GET['srcdir'].$_GET['file']);
				$file = $_GET['file'];
				$dest = Files::makeFile($this->getImagesDir(), $_GET['dir']);
				return Files::copyFile($src,$dest,$file);
			break;
			case 'copyDir':
				$basePath = $this->getImagesDir();
				$src = $_GET['srcdir'].$_GET['file'];
				$dest = $_GET['dir'].$_GET['file'];
				return Files::copyDir($basePath,$src,$dest);
			break;
			case 'moveFile':
				$src = Files::makeFile($this->getImagesDir(), $_GET['srcdir'].$_GET['file']);
				$dest = Files::makeFile($this->getImagesDir(), $_GET['dir'].$_GET['file']);
				return Files::rename($src,$dest);
			break;
			case 'moveDir':
				$src = Files::makeFile($this->getImagesDir(), $_GET['srcdir'].$_GET['file']);
				$dest = Files::makeFile($this->getImagesDir(), $_GET['dir'].$_GET['file']);
				return Files::rename($src,$dest);
			break;
		}
	}
}

?>
