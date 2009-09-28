SaveSubmit for Xinha

developed by Raimund Meyer (ray) xinha @ raimundmeyer.de

Registers a button for submiting the Xinha form using asynchronous
postback for sending the data to the server

Usage: This should be a drop-in replacement for a normal submit button.
While saving a message is displayed to inform the user what's going on.
On successful transmission the output of the target script is shown, so it should print some information
about the success of saving.

ATTENTION: The data sent by this method is always UTF-8 encoded, regardless of the actual charset used. So, if you 
are using a different encoding you have to convert on the server side.

