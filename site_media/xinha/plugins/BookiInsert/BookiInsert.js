function BookiInsert(editor) {
    this.editor = editor;

    var cfg = editor.config;
    var self = this;
    
    cfg.registerButton({
        id       : "bookiinsert",
        tooltip  : HTMLArea._lc("Insert image"),
        image    : editor.imgURL("ed_image.gif", "BookiInsert"),
        textMode : false,

        action   : function(editor) {
	    self.buttonPress(editor);
        }
    });
    cfg.addToolbarElement("bookiinsert", "inserthorizontalrule", 1);
}



BookiInsert._pluginInfo = {
    name          : "Booki Insert",
    version       : "1.0",
    developer     : "Aleksandar Erkalovic",
    developer_url : "http://www.binarni.net/",
    license       : "none"
};

Xinha.Config.prototype.ImageManager = {
    backend: Xinha.getPluginDir("BookiInsert") + "/edit.html?",
    backend_data: null,
    backend_config: null,
    backend_config_hash: null,
    backend_config_secret_key_location: "Xinha:ImageManager"
};

    
BookiInsert.prototype.buttonPress = function(editor) {
    $.booki.editor.upload.setEditor(editor);
    $("#insertattachment").dialog("open");
}

/*

function ImageManager(a) {}
ImageManager._pluginInfo = {
    name: "ImageManager",
    version: "1.0",
    developer: "Xiang Wei Zhuo",
    developer_url: "http://www.zhuo.org/htmlarea/",
    license: "htmlArea"
};
Xinha.Config.prototype.ImageManager = {
    backend: Xinha.getPluginDir("ImageManager") + "/backend.php?__plugin=ImageManager&",
    backend_data: null,
    backend_config: null,
    backend_config_hash: null,
    backend_config_secret_key_location: "Xinha:ImageManager"
};
Xinha.prototype._insertImage = function (f) {
    var d = this;
    var g = null;
    if (typeof f == "undefined") {
        f = this.getParentElement();
        if (f && !/^img$/i.test(f.tagName)) {
            f = null
        }
    }
    if (f) {
        g = {
            f_url: Xinha.is_ie ? f.src : f.src,
            f_alt: f.alt,
            f_border: f.style.borderWidth ? f.style.borderWidth : f.border,
            f_align: f.align,
            f_padding: f.style.padding,
            f_margin: f.style.margin,
            f_width: f.width,
            f_height: f.height,
            f_backgroundColor: f.style.backgroundColor,
            f_borderColor: f.style.borderColor
        };

        function a(h) {
            if (/ /.test(h)) {
                var l = h.split(" ");
                var k = true;
                for (var j = 1; j < l.length; j++) {
                    if (l[0] != l[j]) {
                        k = false;
                        break
                    }
                }
                if (k) {
                    h = l[0]
                }
            }
            return h
        }
        g.f_border = a(g.f_border);
        g.f_padding = a(g.f_padding);
        g.f_margin = a(g.f_margin);

        function e(k) {
            if (typeof k == "string" && /, /.test.color) {
                k = k.replace(/, /, ",")
            }
            if (typeof k == "string" && / /.test.color) {
                var h = k.split(" ");
                var j = "";
                for (var l = 0; l < h.length; l++) {
                    j += Xinha._colorToRgb(h[l]);
                    if (l + 1 < h.length) {
                        j += " "
                    }
                }
                return j
            }
            return Xinha._colorToRgb(k)
        }
        g.f_backgroundColor = e(g.f_backgroundColor);
        g.f_borderColor = e(g.f_borderColor)
    }
    var c = d.config.ImageManager.backend + "__function=manager";
    if (d.config.ImageManager.backend_config != null) {
        c += "&backend_config=" + encodeURIComponent(d.config.ImageManager.backend_config);
        c += "&backend_config_hash=" + encodeURIComponent(d.config.ImageManager.backend_config_hash);
        c += "&backend_config_secret_key_location=" + encodeURIComponent(d.config.ImageManager.backend_config_secret_key_location)
    }
    if (d.config.ImageManager.backend_data != null) {
        for (var b in d.config.ImageManager.backend_data) {
            c += "&" + b + "=" + encodeURIComponent(d.config.ImageManager.backend_data[b])
        }
    }
    Dialog(c, function (l) {
        if (!l) {
            return false
        }
        var i = f;
        if (!i) {
            if (Xinha.is_ie) {
                var k = d._getSelection();
                var h = d._createRange(k);
                d._doc.execCommand("insertimage", false, l.f_url);
                i = h.parentElement();
                if (i.tagName.toLowerCase() != "img") {
                    i = i.previousSibling
                }
            } else {
                i = document.createElement("img");
                i.src = l.f_url;
                d.insertNodeAtSelection(i)
            }
        } else {
            i.src = l.f_url
        }
        for (field in l) {
            var j = l[field];
            switch (field) {
            case "f_alt":
                i.alt = j;
                break;
            case "f_border":
                if (j.length) {
                    i.style.borderWidth = /[^0-9]/.test(j) ? j : (parseInt(j) + "px");
                    if (i.style.borderWidth && !i.style.borderStyle) {
                        i.style.borderStyle = "solid"
                    }
                } else {
                    i.style.borderWidth = "";
                    i.style.borderStyle = ""
                }
                break;
            case "f_borderColor":
                i.style.borderColor = j;
                break;
            case "f_backgroundColor":
                i.style.backgroundColor = j;
                break;
            case "f_padding":
                if (j.length) {
                    i.style.padding = /[^0-9]/.test(j) ? j : (parseInt(j) + "px")
                } else {
                    i.style.padding = ""
                }
                break;
            case "f_margin":
                if (j.length) {
                    i.style.margin = /[^0-9]/.test(j) ? j : (parseInt(j) + "px")
                } else {
                    i.style.margin = ""
                }
                break;
            case "f_align":
                i.align = j;
                break;
            case "f_width":
                if (!isNaN(parseInt(j))) {
                    i.width = parseInt(j)
                } else {
                    i.width = ""
                }
                break;
            case "f_height":
                if (!isNaN(parseInt(j))) {
                    i.height = parseInt(j)
                } else {
                    i.height = ""
                }
                break
            }
        }
    },
    g)
};


*/
