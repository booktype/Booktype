<?php
// REVISION HISTORY:
//
// 2005-08-17 YmL:
//	.	security fix on unchecked variables. Original author missed quite a few
//		holes.

  umask(000);
  $temptext = tempnam('/tmp', 'spell_');
  if ((!isset($_POST['dictionary'])) || (strlen(trim($_POST['dictionary'])) < 1))
  {
      $lang = 'en_GB';
  }
  else
  {
      $lang = $_POST['dictionary'];
  }  
  $lang = preg_replace('/[^a-z0-9_]/i', '', $lang);
  
  $aspell      = 'aspell';
  $aspell_args = '-a --lang=' . $lang;

  if(DIRECTORY_SEPARATOR == '\\') //windows
  {
    $aspell         = 'C:\Progra~1\Aspell\bin\aspell.exe';
  }
  else //linux
  {
    // See if there is a local install of aspell here
    if(file_exists(dirname(__FILE__) . '/aspell/bin/aspell'))
    {
      putenv('PATH=' . dirname(__FILE__) . '/aspell/bin:' . getenv('PATH'));
      putenv('LD_LIBRARY_PATH=' . dirname(__FILE__) . '/aspell/lib:' . getenv('LD_LIBRARY_PATH'));
      $dicfil = dirname(__FILE__) .'/aspell/lib/' . preg_replace('/^.*\/lib\/(aspell\S*)\n.*/s', '$1', `aspell config dict-dir`);
      $aspell_args .= ' --dict-dir=' . $dicfil . ' --add-filter-path=' . $dicfil ;
    }
  }


  // Old aspell doesn't know about encoding, which means that unicode will be broke, but
  // we should at least let it try.
  preg_match('/really aspell ([0-9]+)\.([0-9]+)(?:\.([0-9]+))?/i', `$aspell version`, $aVer);

  $aVer = array('major' => (int)$aVer[1], 'minor' => (int)$aVer[2], 'release' => (int)@$aVer[3]);
  if($aVer['major'] >= 0 && $aVer['minor'] >= 60)
  {
    $aspell_args   .= ' -H --encoding=utf-8';
  }
  elseif(preg_match('/--encoding/', shell_exec('aspell 2>&1')))
  {
    $aspell_args   .= ' --mode=none --add-filter=sgml --encoding=utf-8';
  }
  else
  {
    $aspell_args   .= ' --mode=none --add-filter=sgml';
  }

  // Personal dictionaries
  $p_dicts_path = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'personal_dicts';

  if(isset($_REQUEST['p_dicts_path']) && file_exists($_REQUEST['p_dicts_path']) && is_writable($_REQUEST['p_dicts_path']))
  {
    if(!isset($_REQUEST['p_dicts_name']))
    {
      if(isset($_COOKIE['SpellChecker_p_dicts_name']))
      {
        $_REQUEST['p_dicts_name'] = $_COOKIE['SpellChecker_p_dicts_name'];
      }
      else
      {
        $_REQUEST['p_dicts_name'] = uniqid('dict');
        setcookie('SpellChecker_p_dicts_name', $_REQUEST['p_dicts_name'], time() + 60*60*24*365*10);
      }
    }    
    $p_dict_path = $_REQUEST['p_dicts_path'] . DIRECTORY_SEPARATOR . preg_replace('/[^a-z0-9_]/i', '', $_REQUEST['p_dicts_name']);

    if(!file_exists($p_dict_path))
    {
	 	// since there is a single directory for all users this could end up containing
		// quite a few subdirectories. To prevent a DOS situation we'll limit the 
		// total directories created to 2000 (arbitrary). Adjust to suit your installation.

		$count = 0;

		if( $dir = @opendir( $p_dicts_path ) )
			{

			while( FALSE !== ($file = readdir($dir)) )
				{
				$count++;
				}
			}

		// TODO: make this a config value.

		if ( $count > 2000 )
			{

			// either very heavy use or a DOS attempt

			die();

			}

      mkdir($p_dict_path);
      chmod($p_dict_path, 02770);
    }

    if(file_exists($p_dict_path) && is_writable($p_dict_path))
    {
      // Good To Go!
      $aspell_args .= ' --home-dir=' . $p_dict_path ;
    }
  }

// as an additional precaution check the aspell_args for illegal 
// characters
  $aspell_args = preg_replace( "/[|><;\$]+/", '', $aspell_args );
  $aspelldictionaries = "$aspell dump dicts";
  $aspellcommand      = "$aspell $aspell_args < $temptext";


?>
