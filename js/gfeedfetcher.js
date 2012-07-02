// -------------------------------------------------------------------
// gAjax RSS Feeds Displayer- By Dynamic Drive, available at: http://www.dynamicdrive.com
// Created: July 17th, 2007
// Updated June 14th, 10': Fixed issue in IE where labels would sometimes be associated with the incorrect feed items
// -------------------------------------------------------------------

var gfeedfetcher_loading_image="../img/indicator.gif" //Full URL to "loading" image. No need to config after this line!!

google.load("feeds", "1") //Load Google Ajax Feed API (version 1)

function gfeedfetcher(divid, divClass, linktarget){
	this.linktarget=linktarget || "" //link target of RSS entries
	this.feedlabels=[] //array holding lables for each RSS feed
	this.feedurls=[]
	this.feeds=[] //array holding combined RSS feeds' entries from Feed API (result.feed.entries)
	this.feedsfetched=0 //number of feeds fetched
	this.feedlimit=5
	this.showoptions="" //Optional components of RSS entry to show (none by default)
	this.sortstring="date" //sort by "date" by default
	document.write('<div id="'+divid+'" class="'+divClass+'"></div>') //output div to contain RSS entries
	this.feedcontainer=document.getElementById(divid)
	this.itemcontainer="<li>" //default element wrapping around each RSS entry item
}

gfeedfetcher.prototype.addFeed=function(label, url){
	this.feedlabels[this.feedlabels.length]=label
	this.feedurls[this.feedurls.length]=url
}

gfeedfetcher.prototype.filterfeed=function(feedlimit, sortstr){
	this.feedlimit=feedlimit
	if (typeof sortstr!="undefined")
	this.sortstring=sortstr
}

gfeedfetcher.prototype.displayoptions=function(parts){
	this.showoptions=parts //set RSS entry options to show ("date, datetime, time, snippet, label, description")
}

gfeedfetcher.prototype.setentrycontainer=function(containerstr){  //set element that should wrap around each RSS entry item
this.itemcontainer="<"+containerstr.toLowerCase()+">"
}

gfeedfetcher.prototype.init=function(){
	this.feedsfetched=0 //reset number of feeds fetched to 0 (in case init() is called more than once)
	this.feeds=[] //reset feeds[] array to empty (in case init() is called more than once)
	this.feedcontainer.innerHTML='<p><img src="'+gfeedfetcher_loading_image+'" /> Retrieving RSS feed(s)</p>'
	var displayer=this
	for (var i=0; i<this.feedurls.length; i++){ //loop through the specified RSS feeds' URLs
		var feedpointer=new google.feeds.Feed(this.feedurls[i]) //create new instance of Google Ajax Feed API
		var items_to_show=(this.feedlimit<=this.feedurls.length)? 1 : Math.floor(this.feedlimit/this.feedurls.length) //Calculate # of entries to show for each RSS feed
		if (this.feedlimit%this.feedurls.length>0 && this.feedlimit>this.feedurls.length && i==this.feedurls.length-1) //If this is the last RSS feed, and feedlimit/feedurls.length yields a remainder
			items_to_show+=(this.feedlimit%this.feedurls.length) //Add that remainder to the number of entries to show for last RSS feed
		feedpointer.setNumEntries(items_to_show) //set number of items to display
		feedpointer.load(function(label){
			return function(r){
				displayer._fetch_data_as_array(r, label)
			}
		}(this.feedlabels[i])) //call Feed.load() to retrieve and output RSS feed.
	}
}


gfeedfetcher._formatdate=function(datestr, showoptions){
	var itemdate=new Date(datestr)
	var parseddate=(showoptions.indexOf("datetime")!=-1)? itemdate.toLocaleString() : (showoptions.indexOf("date")!=-1)? itemdate.toLocaleDateString() : (showoptions.indexOf("time")!=-1)? itemdate.toLocaleTimeString() : ""
	return "<span class='datefield'>"+parseddate+"</span>"
}

gfeedfetcher._sortarray=function(arr, sortstr){
	var sortstr=(sortstr=="label")? "ddlabel" : sortstr //change "label" string (if entered) to "ddlabel" instead, for internal use
	if (sortstr=="title" || sortstr=="ddlabel"){ //sort array by "title" or "ddlabel" property of RSS feed entries[]
		arr.sort(function(a,b){
		var fielda=a[sortstr].toLowerCase()
		var fieldb=b[sortstr].toLowerCase()
		return (fielda<fieldb)? -1 : (fielda>fieldb)? 1 : 0
		})
	}
	else{ //else, sort by "publishedDate" property (using error handling, as "publishedDate" may not be a valid date str if an error has occured while getting feed
		try{
			arr.sort(function(a,b){return new Date(b.publishedDate)-new Date(a.publishedDate)})
		}
		catch(err){}
	}
}

gfeedfetcher.prototype._fetch_data_as_array=function(result, ddlabel){	
	var thisfeed=(!result.error)? result.feed.entries : "" //get all feed entries as a JSON array or "" if failed
	if (thisfeed==""){ //if error has occured fetching feed
		alert("Some blog posts could not be loaded: "+result.error.message)
	}
	for (var i=0; i<thisfeed.length; i++){ //For each entry within feed
		result.feed.entries[i].ddlabel=ddlabel //extend it with a "ddlabel" property
	}
	this.feeds=this.feeds.concat(thisfeed) //add entry to array holding all feed entries
	this._signaldownloadcomplete() //signal the retrieval of this feed as complete (and move on to next one if defined)
}

gfeedfetcher.prototype._signaldownloadcomplete=function(){
	this.feedsfetched+=1
	if (this.feedsfetched==this.feedurls.length) //if all feeds fetched
		this._displayresult(this.feeds) //display results
}


gfeedfetcher.prototype._displayresult=function(feeds){
	var rssoutput=(this.itemcontainer=="<li>")? "<ul>\n" : ""
	gfeedfetcher._sortarray(feeds, this.sortstring)
	for (var i=0; i<feeds.length; i++){
		var itemtitle="<a rel=\"nofollow\" href=\"" + feeds[i].link + "\" target=\"" + this.linktarget + "\" class=\"titlefield\">" + feeds[i].title + "</a>"
		var itemlabel=/label/i.test(this.showoptions)? '<span class="labelfield">['+this.feeds[i].ddlabel+']</span>' : " "
		var itemdate=gfeedfetcher._formatdate(feeds[i].publishedDate, this.showoptions)
		var itemdescription=/description/i.test(this.showoptions)? "<br />"+feeds[i].content : /snippet/i.test(this.showoptions)? "<br />"+feeds[i].contentSnippet  : ""
		rssoutput+=this.itemcontainer + itemtitle + " " + itemlabel + " " + itemdate + "\n" + itemdescription + this.itemcontainer.replace("<", "</") + "\n\n"
	}
	rssoutput+=(this.itemcontainer=="<li>")? "</ul>" : ""
	this.feedcontainer.innerHTML=rssoutput
}

