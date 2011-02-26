By default the smileys are hosted on an external server. If you would like to put them on your own server, you can download a zip file from here:
http://www.x-webservice.net/storage/xinha/plugins/InsertSmiley/smileys.zip

1. Extract the file to your server
2. Change xinha_config.InsertSmiley.smileyURL to the appropriate path (with trailing slash), e.g.
   
   xinha_config.InsertSmiley.smileyURL = "/smileys/";
   
 You can also reduce/expand/replace the list of smileys with your own files by editing the file smileys.txt in the plugins's folder.