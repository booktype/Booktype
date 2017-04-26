importScripts('/static/edit/js/draft/autobahn.js');
importScripts('/static/edit/js/draft/localforage.js')


var session_key = "{{session_key}}";

var csrf_token = "{{csrf_token}}";

var book_id = "{{book.id}}"
function onchallenge (session, method, extra) {

   console.log("onchallenge", method, extra);

   if (method === "wampcra") {

      console.log("authenticating via '" + method + "' and challenge '" + extra.challenge + "'");

      return autobahn.auth_cra.sign(session_key, extra.challenge);

   } else {
      throw "don't know how to authenticate using '" + method + "'";
   }
};
var connection = new autobahn.Connection({
   url: "ws://127.0.0.1:8080/ws",
   realm: "booktype",
   authid: session_key+"_"+csrf_token,
   authmethods: ["wampcra"],
   onchallenge: onchallenge
});

connection.onclose = function (reason, details) {
   console.log("Connection lost:", reason, details);
};

onmessage = function(e){
  switch(e.data.command){
    case "createorload":
    console.log(e.data)
      this.db = localforage.createInstance({
        name: book_id +"_"+e.data.hash.replace("#edit/","")
      })
      this.hash = e.data.hash
      this.pathname = e.data.pathname
      this.name = e.data.name
      var that = this
      this.db.getItem("content", function(err,value){
        var schema = {
          blockMap: ["key", "data", "text", "characterList", "depth", "type"],
          entityMap: ["type", "data", "mutability"]
        }
        if(err | !value){
          var newContent = {
            blockMap: [{
              key: "first",
              data: {},
              text: "",
              characterList:[],
              depth: 0,
              type: 'unstyled'
            }],
            entityMap: []
          }
          that.document = new DocumentNew(that.name, newContent, schema)
          that.db.setItem("content", that.document.content)
        }else{
          that.document = new DocumentNew(that.name, value)
          that.document.setContent(value)
        }
        that.connector = new Connector(that.document)
        that.document.onUpdate = function(patch){
          if(that.sync)
            that.connector.sendPatch(patch)
        }
        that.connector.onUpdate = function(patch){
          if(that.sync){
            that.document.patch(patch[0])
            that.db.setItem("content", that.document.content)
            postMessage({
              command: "updatecontent",
              content: that.document.getContent()
            })
          }
        }
        postMessage({
          command: "newcontent",
          content: that.document.getContent()
        })
      })
      break;
  }
}

connection.open();
