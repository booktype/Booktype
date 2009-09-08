<?php 
/*
This ddt library is released under the terms of the HTMLArea license. 
See license.txt that is shipped with Xinha.
*/

// must be included after the configuration has been loaded.

if ( ! defined( "IM_CONFIG_LOADED" ) )
	die( "sorry" );

/**
* Debug and Error Message functions.
*
* These functions implement a procedural version of the formVista DDT debug
* message system.
*
* @package formVista
* @subpackage lib
* @copyright DTLink, LLC 2005
* @author Yermo Lamers
* @see http://www.formvista.com/contact.html
*/

// REVISION HISTORY:
//
// 26 Jan 2001 YmL:
//		. initial revision
//
// 2002-06-19 YmL:
//		. added	logging	debug and error	messages to a file.
//
// 2004-02-06 YmL:
//	.	added a newline to generated messages.
//
// 2005-01-09 YmL:
//	.	now checks global $fvDEBUG[ "logfile" ] setting for 
//		logfile to output to. 
//	.	dumping to file has not been combined into a dumpmsg 
//		method.
//
// 2005-02-25 YmL:
//	.	added _error() support for cmdLine programs.
//
// 2005-03-20 YmL:
//	.	changed license for this file to HTMLArea from RPL.
//	.	quick hack to repurpose for Xinha.
//
// -------------------------------------------------------

/**
* dumps message to stdout or log file depending upon global.
*
* checks $fvDEBUG["logfile"] global for name of file to dump
* messages to. Opens the file once.
*/

function dumpmsg( $msgline )
{

global $fvDEBUG;

if ( @$fvDEBUG[ "logfile" ] != NULL )
	{

	// only open the file once and store the handle in the global
	// fvDEBUG array .. for now.

	if ( @$fvDEBUG[ "logfile_fp" ] == NULL )
		{

		// we clear out the debug file on each run.

		if (( $fvDEBUG[ "logfile_fp" ] = fopen( $fvDEBUG[ "logfile" ], "a" )) == NULL )
			{
			die( "ddt(): unable to open debug log" );
			return  false ;
			}
		}

	fputs( $fvDEBUG[ "logfile_fp" ], "$msgline" );
	fflush( $fvDEBUG[ "logfile_fp" ] );

	}
else
	{
	echo $msgline;
	}

}	// end of dumpmsg.

/**
* displays a formatted debugging message.
*
* If ddtOn() was called, outputs a formatted debugging message.
*
* @param string $file filename, usually __FILE__
* @param string $line line number in file, usually __LINE__
* @param string $msg debugging message to display
*/

function _ddt( $file, $line, $msg )
{

global $_DDT;
global $_DDT_DEBUG_LOG;
global $_DDT_CMDLINE;

$basename = basename( $file );

if ( @$_DDT == "yes" )
	{

	if ( @$_DDT_CMDLINE == "yes" )
		{
		dumpmsg( basename( $file ) . ":$line: $msg \n" );
		flush();

		}
	else
		{
		dumpmsg( "<p>$basename:$line: $msg</p>\n" );
		}
	}

}	// end of _ddt

/**
* displays a formatted dump of an associative array.
*
* If ddtOn() was called, outputs a formatted debugging message showing 
* contents of array.
*
* @param string $file filename, usually __FILE__
* @param string $line line number in file, usually __LINE__
* @param string $msg debugging message to display
* @param array $array_var array to dump.
*/

function _ddtArray( $file, $line, $msg,	$array_var )
{

global $_DDT;

if ( $_DDT == "yes" )
	{

	dumpmsg( "<h2>$file:$line: $msg</h2>" );
	
	foreach	( $array_var as	$name => $value	)
		{
		dumpmsg( "<p><b>$name</b> => <b>$value</b>\n" );
		}
	}

}	// end of _ddtArray

// -----------------------------------------------------------------

/**
* Central Error Function.
*
* Displays a formatted error message to the user.
* If the global _DDT_ERROR_LOG is set the error message is dumped 
* to that file	instead	of being displayed to the user.
*/

function _error( $file,	$line, $msg )
{

global $_DDT_ERROR_LOG;
global $_DDT_CMDLINE;

if ( @$_DDT_ERROR_LOG == NULL )
	{

	if ( @$_DDT_CMDLINE == "yes" )
		{
		echo basename($file) . ":$line: $msg\n";
		}
	else
		{
		echo "<h2>$file:$line: $msg</h2>";
		}
	}
else
	{
	 
	if (( $fp = fopen( $_DDT_ERROR_LOG, "a"	)) != NULL )
		{
		fputs( $fp, date("D M j	G:i:s T	Y") . "	- $file:$line: $msg\n" );
		fclose(	$fp );
		}
		
	}
	
}	// end of _error

// ----------------------------------------------------------------------

function errorEcho( $title, $field )
{

global $error_msg;

if ( $error_msg[ $field	] != ""	)
	{
	
	echo "<FONT SIZE=\"+2\"	COLOR=\"RED\">$title</FONT>";
	
	}
else
	{
	
	echo $title;
	
	}
	
}	// end of errorEcho

/**
* turns on procedural debugging.
*
* Causes _ddt() calls to display debugging messages.
*/

function _ddtOn()
{

global $_DDT;

$_DDT =	"yes";

}

/**
* set error message destination.
*
* sets the destination for error messages.
*
* @param string $file full path to errorlog.
*/

function _setErrorLog( $errorLog )
{

global $_DDT_ERROR_LOG;

$_DDT_ERROR_LOG	= $errorLog;

}

/**
* set output file for debugging messages.
*
* sets the destination file for debugging messages.
*
* @param string $file full path to debuglog.
*/

function _setDebugLog( $debugLog )
{

global $fvDEBUG;

$fvDEBUG[ "logfile" ] = $debugLog;

}

/**
* set debugging output style to command line.
*
* tells ddt to format debugging messages for a 
* command line program.
*/

function _ddtSetCmdLine()
{

global $_DDT_CMDLINE;

$_DDT_CMDLINE = "yes";

}

// END

?>
