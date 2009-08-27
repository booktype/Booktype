<?php 
/**
* Unified backend for ExtendedFileManager - copied from ImageManager
*
* Image Manager was originally developed by:
*   Xiang Wei Zhuo, email: xiangweizhuo(at)hotmail.com Wei Shou.
*
* Unified backend sponsored by DTLink Software, http://www.dtlink.com
* Implementation by Yermo Lamers, http://www.formvista.com
*
* (c) DTLink, LLC 2005.
* Distributed under the same terms as Xinha itself.
* This notice MUST stay intact for use (see license.txt).
*
* DESCRIPTION:
*
* Instead of using separate URL's for each function, ImageManager now
* routes all requests to the server through this single, replaceable,
* entry point. backend.php expects at least two URL variable parameters: 
*
* __plugin=ImageManager   for future expansion; identify the plugin being requested.
* __function=thumbs|images|editorFrame|editor|manager  function being called.
*
* Having a single entry point that strictly adheres to a defined interface will 
* make the backend code much easier to maintain and expand. It will make it easier
* on integrators, not to mention it'll make it easier to have separate 
* implementations of the backend in different languages (Perl, Python, ASP, etc.) 
*
* @see config.inc.php
*/

/**
* ImageManager configuration
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

/**
* ImageManager configuration
*/

$formVars = empty($_POST) ? $_GET : $_POST;

// make sure the request is for us (this gives us the ability to eventually organize
// a backend event handler system) For an include file the return doesn't make alot of
// sense but eventually we'll want to turn all of this into at least functions 
// separating out all the presentation HTML from the logic. (Right now all the HTML
// used by ImageManager is in the same files as the PHP code ...)

if ( @$formVars[ "__plugin" ] != "ExtendedFileManager" )
	{
	// not for us.

	return true;
	}

// so we don't have to re-engineer the entire thing right now, since it's probably
// going to get rewritten anyway, we just include the correct file based on the 
// function request.

switch ( @$formVars[ "__function" ] )
	{

	case "editor": 
	case "editorFrame":
	case "manager":
	case "images":
	case "thumbs":
	case "resizer":

		include_once $IMConfig['base_dir'] . '/' . $formVars['__function'] . '.php' ;
		exit();
		
		break;

	default:

		break;

	}	// end of switch.

return false ;

// END

?>