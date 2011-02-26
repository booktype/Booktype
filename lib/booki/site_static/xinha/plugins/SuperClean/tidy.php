<?php
  /** This PHP file is intended for use with XMLHTTPRequest from Xinha
   * it requrns javascript to set the Xinha html with tidied html that is
   * submitted in a $_POST parameter called 'content'
   */

  if(get_magic_quotes_gpc())
  {
    // trigger_error('Magic Quotes GPC is on, cleaning GPC.', E_USER_NOTICE);
    $to_clean = array(&$_GET, &$_POST, &$_REQUEST, &$_COOKIE);
    while(count($to_clean))
    {
      $cleaning =& $to_clean[array_pop(array_keys($to_clean))];
      unset($to_clean[array_pop(array_keys($to_clean))]);
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

  header('Content-Type: text/javascript; charset=utf-8');

  /** Function to POST some data to a URL */
  function PostIt($DataStream, $URL)
  {

//  Strip http:// from the URL if present
    $URL = ereg_replace("^http://", "", $URL);

//  Separate into Host and URI
    $Host = substr($URL, 0, strpos($URL, "/"));
    $URI = strstr($URL, "/");

//  Form up the request body
    $ReqBody = "";
    while (list($key, $val) = each($DataStream)) {
      if ($ReqBody) $ReqBody.= "&";
      $ReqBody.= $key."=".urlencode($val);
    }
    $ContentLength = strlen($ReqBody);

//  Generate the request header
    $ReqHeader =
      "POST $URI HTTP/1.0\n".
      "Host: $Host\n".
      "User-Agent: PostIt\n".
      "Content-Type: application/x-www-form-urlencoded\n".
      "Content-Length: $ContentLength\n\n".
      "$ReqBody\n";

//     echo $ReqHeader;


//  Open the connection to the host
    $socket = fsockopen($Host, 80, $errno, $errstr);
    if (!$socket) {
      $result = "($errno) $errstr";
      return $Result;
    }

    fputs($socket, $ReqHeader);

    $result = '';
    while(!feof($socket))
    {
      $result .= fgets($socket);
    }
    return $result;
  }


  function js_encode($string)
  {
    static $strings = "\\,\",',%,&,<,>,{,},@,\n,\r";

    if(!is_array($strings))
    {
      $tr = array();
      foreach(explode(',', $strings) as $chr)
      {
        $tr[$chr] = sprintf('\x%02X', ord($chr));
      }
      $strings = $tr;
    }

    return strtr($string, $strings);
  }

  // Any errors would screq up our javascript
  error_reporting(0);
  ini_set('display_errors', false);

  if(trim(@$_REQUEST['content']))
  {
    // PHP's urldecode doesn't understand %uHHHH for unicode
    $_REQUEST['content'] = preg_replace('/%u([a-f0-9]{4,4})/ei', 'utf8_chr(0x$1)', $_REQUEST['content']);
    function utf8_chr($num)
    {
      if($num<128)return chr($num);
      if($num<1024)return chr(($num>>6)+192).chr(($num&63)+128);
      if($num<32768)return chr(($num>>12)+224).chr((($num>>6)&63)+128).chr(($num&63)+128);
      if($num<2097152)return chr(($num>>18)+240).chr((($num>>12)&63)+128).chr((($num>>6)&63)+128) .chr(($num&63)+128);
      return '';
    }
    ob_start();
      passthru("echo " .  escapeshellarg($_REQUEST['content']) . " | tidy -q -i -u -wrap 9999 -utf8 -bare -asxhtml 2>/dev/null", $result);
      $content = ob_get_contents();
    ob_end_clean();

    if(strlen($content) < 4)
    {
      // Tidy on the local machine failed, try a post
      $res_1
        = PostIt(
          array
            (
              '_function' => 'tidy',
              '_html'   => $_REQUEST['content'],
              'char-encoding' => 'utf8',
              '_output'       => 'warn',
              'indent'        => 'auto',
              'wrap'          => 9999,
              'break-before-br' => 'y',
              'bare'          => 'n',
              'word-2000'     => 'n',
              'drop-empty-paras' => 'y',
              'drop-font-tags' => 'n',

            ),
          'http://infohound.net/tidy/tidy.pl');

      if(preg_match('/<a href="([^"]+)" title="Save the tidied HTML/', $res_1, $m))
      {
        $tgt = strtr($m[1], array_flip(get_html_translation_table(HTML_ENTITIES)));
        $content = implode('', file('http://infohound.net/tidy/' . $tgt));
      }
    }

    if(strlen($content) && ! preg_match('/<\/body>/i', $_REQUEST['content']))
    {
      if( preg_match('/<body[^>]*>(.*)<\/body>/is', $content, $matches) )
      {
        $content = $matches[1];
      }
    }
    elseif(!strlen($content))
    {
      $content = $_REQUEST['content'];
    }

    if($content)
    {
      ?>
      {action:'setHTML',value:'<?php echo js_encode($content) ?>'};
      <?php
    }
    else
    {
      ?>
      {action:'alert',value:'Tidy failed.  Check your HTML for syntax errors.'};
      <?php
    }
  }
  else
  {
    ?>
    {action:'alert',value:"You don't have anything to tidy!"}
    <?php
  }

?>
