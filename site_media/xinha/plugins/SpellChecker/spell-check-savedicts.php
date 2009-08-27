<?php
  require_once(dirname(__FILE__) . DIRECTORY_SEPARATOR . 'aspell_setup.php');


  $to_p_dict = $_REQUEST['to_p_dict'] ? $_REQUEST['to_p_dict'] : array();
  $to_r_list = $_REQUEST['to_r_list'] ? $_REQUEST['to_r_list'] : array();
print_r($to_r_list);
  if($to_p_dict || $to_r_list)
  {
    if($fh = fopen($temptext, 'w'))
    {
      foreach($to_p_dict as $personal_word)
      {
        $cmd = '&' . $personal_word . "\n";
        echo $cmd;
        fwrite($fh, $cmd, strlen($cmd));
      }

      foreach($to_r_list as $replace_pair)
      {
        $cmd = '$$ra ' . $replace_pair[0] . ' , ' . $replace_pair[1] . "\n";
        echo $cmd;
        fwrite($fh, $cmd, strlen($cmd));
      }
      $cmd = "#\n";
      echo $cmd;
      fwrite($fh, $cmd, strlen($cmd));
      fclose($fh);
    }
    else
    {
      die("Can't Write");
    }
    echo $aspellcommand."\n";
    echo shell_exec($aspellcommand . ' 2>&1');
    unlink($temptext);
  }
?>