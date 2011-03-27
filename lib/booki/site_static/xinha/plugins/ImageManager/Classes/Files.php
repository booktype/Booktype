<?php
/**
 * File Utilities.
 * @author $Author:koto $
 * @version $Id:Files.php 841 2007-05-27 13:31:51Z koto $
 * @package ImageManager
 */

define('FILE_ERROR_NO_SOURCE', 100);
define('FILE_ERROR_COPY_FAILED', 101);
define('FILE_ERROR_DST_DIR_FAILED', 102);
define('FILE_COPY_OK', 103);
define('FILE_ERROR_DST_DIR_EXIST', 104);

/**
 * File Utilities
 * @author $Author:koto $
 * @version $Id:Files.php 841 2007-05-27 13:31:51Z koto $
 * @package ImageManager
 * @subpackage files
 */
class Files 
{
	
	/**
	 * Copy a file from source to destination. If unique == true, then if
	 * the destination exists, it will be renamed by appending an increamenting 
	 * counting number.
	 * @param string $source where the file is from, full path to the files required
	 * @param string $destination_file name of the new file, just the filename
	 * @param string $destination_dir where the files, just the destination dir,
	 * e.g., /www/html/gallery/
	 * @param boolean $unique create unique destination file if true.
	 * @return string the new copied filename, else error if anything goes bad.
	 */
	function copyFile($source, $destination_dir, $destination_file, $unique=true) 
	{
		if(!is_uploaded_file($source) && !(file_exists($source) && is_file($source))) 
			return FILE_ERROR_NO_SOURCE;

		$destination_dir = Files::fixPath($destination_dir);

		if(!is_dir($destination_dir)) 
			Return FILE_ERROR_DST_DIR_FAILED;

		$filename = Files::escape($destination_file);

		if($unique) 
		{
			$dotIndex = strrpos($destination_file, '.');
			$ext = '';
			if(is_int($dotIndex)) 
			{
				$ext = substr($destination_file, $dotIndex);
				$base = substr($destination_file, 0, $dotIndex);
			}
			$counter = 0;
			while(is_file($destination_dir.$filename)) 
			{
				$counter++;
				$filename = $base.'_'.$counter.$ext;
			}
		}

		if (!copy($source, $destination_dir.$filename))
			return FILE_ERROR_COPY_FAILED;
		
		//verify that it copied, new file must exists
		if (is_file($destination_dir.$filename))
			Return $filename;
		else
			return FILE_ERROR_COPY_FAILED;
	}

	/**
	 * Create a new folder.
	 * @param string $newFolder specifiy the full path of the new folder.
	 * @return boolean true if the new folder is created, false otherwise.
	 */
	function createFolder($newFolder) 
	{
		mkdir ($newFolder, 0777);
		return chmod($newFolder, 0777);
	}


	/**
	 * Escape the filenames, any non-word characters will be
	 * replaced by an underscore.
	 * @param string $filename the orginal filename
	 * @return string the escaped safe filename
	 */
	function escape($filename)
	{
		Return preg_replace('/[^\w\._]/', '_', $filename);
	}

	/**
	 * Delete a file.
	 * @param string $file file to be deleted
	 * @return boolean true if deleted, false otherwise.
	 */
	function delFile($file) 
	{
		if(is_file($file)) 
			Return unlink($file);
		else
			Return false;
	}

	/**
	 * Delete folder(s), can delete recursively.
	 * @param string $folder the folder to be deleted.
	 * @param boolean $recursive if true, all files and sub-directories
	 * are delete. If false, tries to delete the folder, can throw
	 * error if the directory is not empty.
	 * @return boolean true if deleted.
	 */
	function delFolder($folder, $recursive=false) 
	{
		$deleted = true;
		if($recursive) 
		{
			$d = dir($folder);
			while (false !== ($entry = $d->read())) 
			{
				if ($entry != '.' && $entry != '..')
				{
					$obj = Files::fixPath($folder).$entry;
					//var_dump($obj);
					if (is_file($obj))
					{
						$deleted &= Files::delFile($obj);					
					}
					else if(is_dir($obj))
					{
						$deleted &= Files::delFolder($obj, $recursive);
					}
					
				}
			}
			$d->close();

		}

		//$folder= $folder.'/thumbs';
		//var_dump($folder);
		if(is_dir($folder)) 
			$deleted &= rmdir($folder);
		else
			$deleted &= false;

		Return $deleted;
	}

	/**
	 * Append a / to the path if required.
	 * @param string $path the path
	 * @return string path with trailing /
	 */
	function fixPath($path) 
	{
		//append a slash to the path if it doesn't exists.
		if(!(substr($path,-1) == '/'))
			$path .= '/';
		Return $path;
	}

	/**
	 * Concat two paths together. Basically $pathA+$pathB
	 * @param string $pathA path one
	 * @param string $pathB path two
	 * @return string a trailing slash combinded path.
	 */
	function makePath($pathA, $pathB) 
	{
		$pathA = Files::fixPath($pathA);
		if(substr($pathB,0,1)=='/')
			$pathB = substr($pathB,1);
		Return Files::fixPath($pathA.$pathB);
	}

	/**
	 * Similar to makePath, but the second parameter
	 * is not only a path, it may contain say a file ending.
	 * @param string $pathA the leading path
	 * @param string $pathB the ending path with file
	 * @return string combined file path.
	 */
	function makeFile($pathA, $pathB) 
	{		
		$pathA = Files::fixPath($pathA);
		if(substr($pathB,0,1)=='/')
			$pathB = substr($pathB,1);
		
		Return $pathA.$pathB;
	}

	
	/**
	 * Format the file size, limits to Mb.
	 * @param int $size the raw filesize
	 * @return string formated file size.
	 */
	function formatSize($size) 
	{
		if($size < 1024) 
			return $size.' bytes';	
		else if($size >= 1024 && $size < 1024*1024) 
			return sprintf('%01.2f',$size/1024.0).' KB';
		else
			return sprintf('%01.2f',$size/(1024.0*1024)).' MB';
	}

	/**
	 * Returns size of a directory, with all file & subdirectory
	 * sizes added up
	 * @param string dir path
	 * @return int
	 */
	function dirSize($dirName = '.')
	{
		$dir  = dir($dirName);
		$size = 0;

		while ($file = $dir->read()) {
			if ($file != '.' && $file != '..')
			{
				if (is_dir("$dirName$file"))
				{
					$size += Files::dirSize($dirName . '/' . $file);
				}
				else
				{
					$size += filesize($dirName . '/' . $file);
				}
			}
		}
		$dir->close();
		return $size;
	}
	
	/**
	 * Renames file, preserving its directory and extension
	 * @param string $oldPath path to the old existing file
	 * @param string new filename (just the name, without path or extension)
	 * @author Krzysztof Kotowicz <koto@webworkers.pl>
	 */
	function renameFile($oldPath, $newName) {

		if(!(file_exists($oldPath) && is_file($oldPath)))
			return FILE_ERROR_NO_SOURCE;

		$oldFileParts = pathinfo($oldPath);

		$newPath = $oldFileParts['dirname'] . '/'
				   . $newName
				   . (!empty($oldFileParts['extension']) ? '.' . $oldFileParts['extension'] : '');

		if (file_exists($newPath))
			return false;

		if (!rename($oldPath, $newPath))
			return FILE_ERROR_COPY_FAILED;

	}
	
	function rename ($oldPath,$newPath)
	{
		if(!(is_dir($oldPath) || is_file($oldPath)))
			return FILE_ERROR_NO_SOURCE;
		
		if (file_exists($newPath))
			return FILE_ERROR_DST_DIR_EXIST;

		$ret = rename($oldPath, $newPath);
		if (!$ret)
			return FILE_ERROR_COPY_FAILED;
		else return FILE_COPY_OK;
	}
	
	/**
	 * copy a directory and all subdirectories and files (recursive)
	 * @author SBoisvert at Don'tSpamMe dot Bryxal dot ca (adapted from php.net)
	 * @author Raimund Meyer
	 * @param string base path
	 * @param string source directory
	 * @param string destination directory
	 * @param bool   overwrite existing files
	 *  
	 * @return mixed bool true on pass, number on fail
	 */
  	function copyDir($basePath, $source, $dest, $overwrite = false)
	{
		if(!is_dir($basePath . $dest))
		{
			if (!@mkdir($basePath . $dest)) return FILE_ERROR_DST_DIR_FAILED;	
		}
		if($handle = opendir($basePath . $source))
		{        // if the folder exploration is sucsessful, continue
			while( ($file = readdir($handle)) !== false)
			{ // as long as storing the next file to $file is successful, continue
				if($file != '.' && $file != '..')
				{
					$path = $source . '/' . $file;
					if(is_file($basePath . $path))
					{
						/*if(!is_file($basePath . $dest . '/' . $file) || $overwrite)
						{
							if(!@copy($basePath . $path, $basePath . $dest . '/' . $file))
							{
							  return FILE_ERROR_COPY_FAILED;
							}
						}*/
						Files::copyFile($basePath . $path, $basePath . $dest . '/', $file, true);
					} 
					elseif(is_dir($basePath . $path))
					{
						if(!is_dir($basePath . $dest . '/' . $file))
						{
							mkdir($basePath . $dest . '/' . $file); // make subdirectory before subdirectory is copied
							Files::copyDir($basePath, $path, $dest . '/' . $file, $overwrite); //recurse!
						}
					}
				}
			}
			closedir($handle);
		}
		return true;
	}
}

?>
