importScripts('msgpack.js')
importScripts('autobahn.js')
importScripts('diff.js')
importScripts('localforage.js')

console.log(window.booktype.session_key)
var connection = new autobahn.Connection({
   url: "ws://127.0.0.1:8080/ws",
   realm: "booktype",
});


function Document(name, content, schema){
  this.name = name
  this.schema = schema
  if(content){
    this.content = {}
    for(var prop in schema){
      this.content[prop] = this.compressAndEncode(content[prop], schema[prop])
    }
  }

}
Document.prototype = {
  setContent: function(content){
    this.content = content
  },
  getContent: function(){
    var decodedContent = {}
    for (var prop in this.content){
      decodedContent[prop] = this.decodeAndDecompress(
                                this.content[prop],
                                this.schema[prop]
                             )
    }
    return decodedContent
  },
  patchContent: function(patch){
    for (var prop in patch){
      this.content[prop] = this.patch(prop, patch[prop])
    }
  },
  updateContent: function(change){
    var patches = {}
    var newContent = {}
    var patchedContent = {}
    for(var prop in this.schema){
      if(change[prop].diffs){
        patches[prop] = this.diff(prop, change[prop])
        // newContent[prop] = this.content[prop]
        //                       .slice(0, change[prop].start)
        //                       .concat(
        //                         this.compressAndEncode(
        //                           change[prop].diffs,
        //                           this.schema[prop]
        //                         )
        //                       )
        //                       .concat(
        //                         this.content[prop].slice(change[prop].end)
        //                       )
        patchedContent[prop] = this.patch(prop, patches[prop])
        // if(patchedContent[prop].toString()!==newContent[prop].toString()){
        //   console.error("Not equal!!!!!!!")
        // }
        this.content[prop] = patchedContent[prop]
    }
  }
    this.onUpdate(patches)
  },
  compressAndEncode: function(array, schema){
    if(!array.length){
      return []
    }

    console.time('compression')
    return array.reduce((compressed,item)=>{
      // var flatItem = []
      // for(var prop_num in schema){
      //   flatItem.push(item[schema[prop_num]])
      // }
      var encoded = msgpack
         .encode(item)
         .reduce(function(arr,arritem){
           arr.push(arritem)
           return arr
         },[])
      compressed.push([999].concat(encoded))
      return compressed
    },[])
    console.timeEnd('compression')
  },
  decodeAndDecompress: function (array, schema){
    if(!array.length){
      return []
    }
    console.log(array)
    return array.reduce(function(decompressed, compressedItem){
      if(compressedItem[0]===999){
        compressedItem = compressedItem.slice(1)
      }
      var item = msgpack.decode(new Uint8Array(compressedItem))

      // var item = {}
      // for(var j in schema){
      //   item[schema[j]] = flatItem[j]
      // }
      if(typeof item.text === "string"){
        decompressed.push(item)
      }else{
        throw "item text is not a string"
      }
      // console.log(item.text)
      return decompressed
    },[])
  },
  diff: function (property, change){
    var previousContent = this.content[property]
    var schema = this.schema[property]
    console.log(change.diffs)
    var items = this.compressAndEncode(change.diffs, schema)
    if(change.end>previousContent.length){
      var previousFragment = previousContent.slice(change.start)
    }else{
      var previousFragment = previousContent.slice(change.start, change.end)
    }
    console.log(previousFragment, items)
    var di = new Diff().diff(
      [].concat.apply([],previousFragment),
      [].concat.apply([],items)
    )
    return [
      change.start,change.end,
      di
    ]
  },
  patch: function (property, patch){
    var currentContent = this.content[property]
    var schema = this.schema[property]
    var start = patch[0]
    var end = patch[1]
    var patch = patch[2]
    if(end> currentContent.length){
      var changedFragment = currentContent.slice(start)
    }else{
      var changedFragment = currentContent.slice(start,end)
    }
    changedFragment = [].concat.apply([],changedFragment)
    var buffers = []
    for(var i in patch){
      var value = patch[i]
      if(typeof value === 'object'){
        buffers = buffers.concat(value)
      }else if(value>0){
        keep = changedFragment.slice(0, value)
        buffers = buffers.concat(keep)
        changedFragment = changedFragment.slice(value)
      }else if(value<0){
        changedFragment = changedFragment.slice(-value)
      }
    }
    var doc = this
    var encodedFragment = buffers.reduce(function(newFragment,item){
      if(item === 999){
        newFragment.push([])
      }else{
        newFragment[newFragment.length-1].push(item)
      }
      return newFragment
    },[])
    return currentContent
      .slice(0,start)
      .concat(encodedFragment)
      .concat(
        currentContent.slice(end)
      )
  },
}

localforage.config({
    name        : 'BobBob',
    version     : 1.0
});


var session = null

function DocumentNew(name, content){
  this.name = name
  this.content = content
}
DocumentNew.prototype.diff = function(change){
  var patch = {}
  for (var prop in change){
    if(change[prop].diffs){
      var previousContent = this.content[prop]
      var newContent = previousContent.slice(0,change[prop].start).concat(
        change[prop].diffs
      ).concat(previousContent.slice(change[prop].end))
      // this.content[prop]= newContent
      console.time("encode")
      // console.log([].slice.call(msgpack.encode(newContent)))
      console.timeEnd("encode")
      patch[prop] = new Diff().diff(
        msgpack.encode(previousContent),
        // .reduce(function(arr, item){arr.push(item);return arr},[]),
        msgpack.encode(newContent)
        // .reduce(function(arr, item){arr.push(item);return arr},[])
      )
    }
  }
  return patch
}
DocumentNew.prototype.setContent = function(content){
  this.content = content
}
DocumentNew.prototype.updateContent = function(change){
  var patch = this.diff(change)
  this.patch(patch)
  this.onUpdate(patch)

}
DocumentNew.prototype.getContent = function(){
  return this.content
}
DocumentNew.prototype.patch = function(patch){
  for(var prop in patch){
    var buffers = []
    if(patch[prop]){
      var currentContent = msgpack.encode(this.content[prop])
      for(var i in patch[prop]){
        var value = patch[prop][i]
        if(typeof value === 'object'){
          buffers = buffers.concat(value)
        }else if(value>0){
          keep = currentContent.slice(0, value)
          buffers = buffers.concat(keep)
          currentContent = currentContent.slice(value)
        }else if(value<0){
          currentContent = currentContent.slice(-value)
        }
      }
      var total_length = 0
      for(let i in buffers){
        total_length+=buffers[i].byteLength
      }
      var newbuffer = new Uint8Array(total_length)
      var current_length = 0
      for(i in buffers){
        newbuffer.set(buffers[i], current_length)
        current_length+= buffers[i].byteLength
      }
      this.content[prop] = msgpack.decode(newbuffer)
    }
  }
}
function Connector(doc){
  var that = this
  connection.onopen = function(session,details){
    that.session = session
    session.call('document.get', [doc.name]).then(
      function(result){
        if(result){
          that.document.setContent(result)
          postMessage({
            command: "newcontent",
            content: that.document.getContent()
          })
        }
      },
      function(error){
      }
    )

    session.subscribe(doc.name, that.onUpdate)
  }
  connection.open()
  this.document = doc
}
Connector.prototype = {
  save: function(){
    this.session.call("document.save", [this.document.name, this.document.content])
  },
  sendPatch: function(patch){
    this.session.publish(this.document.name, [patch])
  },
  receivePatch: function(){},
  sendDocument: function(){
    // this.session.call("savedocument",[this.document.name, this.document.content])
  },
  receiveDocument: function(){}
}

this.sync = true
onmessage = function(e) {
  switch(e.data.command){
    case "createorload":
      this.db = localforage.createInstance({
        name: e.data.name
      })
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
    case "update":
      this.document.updateContent(e.data.change)
      this.db.setItem("content", this.document.content)
      if(this.sync){
      }
      break;
    case "save":
      this.connector.save()
      break;
    case "sync":
      this.sync = e.data.value
      break;
  }
}
