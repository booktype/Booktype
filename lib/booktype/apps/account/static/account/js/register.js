/*
  This file is part of Booktype.
  Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>

  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

(function (win, jquery) {
  'use strict';

  var postURL;
  var postSignURL;
  var redirectURL = '';
  var redirectRegisterURL;

  function showNotification(whr, msg) {
    jquery(whr).find('*').addClass('template');
    jquery(whr).find(msg).removeClass('template');
  }

  var methodsSignin = {
    init : function (options) {
        if (options) {
          postSignURL = options.url || '';
          redirectURL = options.redirect || '';
        }

        return this.each(function () {
          var $this = jquery(this);

          jquery('INPUT[type=submit]', $this).button().click(function () {
            var username = jquery('INPUT[name=username]', $this).val();
            var password = jquery('INPUT[name=password]', $this).val();

            win.booktype.initCSRF();

            jquery.post(postSignURL, {'ajax': '1',
                     'method': 'signin',
                     'username': username,
                     'password': password},

            function (data) {
              var whr = jquery('.notify', $this);
              switch (data.result) {
              case 1: // Everything is ok
                if (redirectURL !== '') {
                  window.location = redirectURL;
                } else {
                  if (typeof data.redirect !== 'undefined') {
                    window.location = data.redirect;
                  } else {
                    var url = jquery.url(window.location.href);
                    window.location = url.param('redirect') || '';
                  }
                }
                return;
              case 2:  // User does not exist
                showNotification(whr, '.no-such-user');
                jquery('INPUT[name=username]', $this).focus().select();
                break;
              case 3: // Wrong password
                showNotification(whr, '.wrong-password');
                jquery('INPUT[name=password]', $this).focus().select();
                break;
              case 4: // User inactive
                showNotification(whr, '.inactive-user');
                jquery('INPUT[name=password]', $this).focus().select();
                break;

              default: // Unknown error
                showNotification(whr, '.unknown-error');
              }

            }, 'json');
          });
          return true;
        });
      }
  };

  var methodsRegister = {
    init : function (options) {
        if (options) {
          postURL = options.url || '';
          redirectRegisterURL = options.redirect || '';
        }

        return this.each(function () {
          var $this = jquery(this);

          jquery('INPUT[type=submit]', $this).button().click(function () {
            var username   = jquery.trim(jquery('INPUT[name=username]', $this).val());
            var email      = jquery.trim(jquery('INPUT[name=email]', $this).val());
            var password   = jquery.trim(jquery('INPUT[name=password]', $this).val());
            var fullname   = jquery.trim(jquery('INPUT[name=fullname]', $this).val());

            var whr = jquery('.notify', $this);
            showNotification(whr, '#clear');

            win.booktype.initCSRF();

            var params = jquery('#formregister').serializeArray();
            params.push({name: 'ajax', value: '1'});
            params.push({name: 'method', value: 'register'});
            params.push({name: 'groups', value: '[]'});
            params.push({name: 'password2', value: password});

            jquery.post(postURL, params,

            function (data) {
              switch (data.result) {
              case 1: // Everything is ok
                window.location = redirectRegisterURL.replace('XXX', username);
                return;

              case 2: // Missing username
                showNotification(whr, '.missing-username');
                jquery('INPUT[name=username]', $this).focus().select();
                break;

              case 3: // Missing email
                showNotification(whr, '.missing-email');
                jquery('INPUT[name=email]', $this).focus().select();
                break;

              case 4: // Missing password
                showNotification(whr, '.missing-password');
                jquery('INPUT[name=password]', $this).focus().select();
                break;

              case 5: // Missing fullname
                showNotification(whr, '.missing-fullname');
                jquery('INPUT[name=fullname]', $this).focus().select();
                break;

              case 6: // Wrong username
                showNotification(whr, '.invalid-username');
                jquery('INPUT[name=username]', $this).focus().select();
                break;

              case 7: // Wrong email
                showNotification(whr, '.invalid-email');
                jquery('INPUT[name=email]', $this).focus().select();
                break;

              case 8: // Password does not match
                showNotification(whr, '.password-mismatch');
                jquery('INPUT[name=password]', $this).focus().select();
                break;

              case 9: // Password too small
                showNotification(whr, '.invalid-password');
                jquery('INPUT[name=password]', $this).focus().select();
                break;

              case 10: // Username exists
                showNotification(whr, '.username-taken');
                jquery('INPUT[name=username]', $this).focus().select();
                break;

              case 11: // Full name too long
                showNotification(whr, '.fullname-toolong');
                jquery('INPUT[name=fullname]', $this).focus().select();
                break;

              case 12: // email already taken
                showNotification(whr, '.email-taken');
                jquery('INPUT[name=email]', $this).focus().select();
                break;


              default: // Unknown error
                showNotification(whr, '.unknown-error');
              }
            }, 'json');

          });
          return true;
        });
      }
  };


  jquery.fn.booktypeRegister = function (method) {
    if (methodsRegister[method]) {
      return methodsRegister[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } else if (typeof method === 'object' || ! method) {
      return methodsRegister.init.apply(this, arguments);
    }
  };

  jquery.fn.booktypeSignin = function (method) {
    if (methodsSignin[method]) {
      return methodsSignin[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } else if (typeof method === 'object' || ! method) {
      return methodsSignin.init.apply(this, arguments);
    }
  };
})(window, jQuery);