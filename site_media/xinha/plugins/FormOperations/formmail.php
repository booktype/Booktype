<?php

  $send_to      = 'Website Enquiries <enquiries@' . preg_replace('/^www./', '', $_SERVER['HTTP_HOST']) . '>';

  $emailfield   = NULL;
  $subjectfield = NULL;
  $namefield    = NULL;

  $when_done_goto    = isset($_REQUEST['when_done_goto']) ? $_REQUEST['when_done_goto'] : NULL;

  if($_POST)
  {
    unset($_POST['when_done_goto']);
    $message    = '';
    $longestKey = 0;
    foreach(array_keys($_POST) as $key)
    {
      $longestKey = max(strlen($key), $longestKey);
    }
    $longestKey = max($longestKey, 15);

    foreach($_POST as $Var => $Val)
    {
      if(!$emailfield)
      {
        if(preg_match('/(^|\s)e-?mail(\s|$)/i', $Var))
        {
          $emailfield = $Var;
        }
      }

      if(!$subjectfield)
      {
        if(preg_match('/(^|\s)subject(\s|$)/i', $Var))
        {
          $subjectfield = $Var;
        }
      }

      if(!$namefield)
      {
        if(preg_match('/(^|\s)from(\s|$)/i', $Var) || preg_match('/(^|\s)name(\s|$)/i', $Var))
        {
          $namefield = $Var;
        }
      }

      if(is_array($Val))
      {
        $Val = implode(', ', $Val);
      }

      $message .= $Var;
      if(strlen($Var) < $longestKey)
      {
        $message .= str_repeat('.', $longestKey - strlen($Var));
      }
      $message .= ':';
      if((64 - max(strlen($Var), $longestKey) < strlen($Val)) || preg_match('/\r?\n/', $Val))
      {
        $message .= "\r\n  ";
        $message .= preg_replace('/\r?\n/', "\r\n  ", wordwrap($Val, 62));
      }
      else
      {
        $message .= ' ' . $Val . "\r\n";
      }
    }

    $subject = $subjectfield ? $_POST[$subjectfield] : 'Enquiry';
    $email   = $emailfield   ? $_POST[$emailfield]   :  $send_to;
    if($namefield)
    {
      $from = $_POST[$namefield] . ' <' . $email . '>';
    }
    else
    {
      $from = 'Website Visitor' . ' <' . $email . '>';
    }

    mail($send_to, $subject, $message, "From: $from");

    if(!$when_done_goto)
    {
      ?>
      <html><head><title>Message Sent</title></head><body><h1>Message Sent</h1></body></html>
      <?php
    }
    else
    {
      header("location: $when_done_goto");
      exit;
    }
  }
?>
