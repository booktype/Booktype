var getAvatar = function (username, size) {
  // MD5 (Message-Digest Algorithm) by WebToolkit
  // http://www.webtoolkit.info/javascript-md5.html
  var size = size || 80;
  return '/_utils/profilethumb/' + username + '/thumbnail.jpg?width=' + size
};


function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}
