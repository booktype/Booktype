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

    var ur = g["f_url"].split('/');
    var fileName = ur[ur.length-1];

    $("#editattachment INPUT[name=f_image]").val('static/'+fileName);
    $("#editattachment INPUT[name=f_alt]").val(g["f_alt"]);
    $("#editattachment INPUT[name=f_border]").val(g["f_border"]);
    $("#editattachment INPUT[name=f_align]").val(g["f_align"]);
    $("#editattachment INPUT[name=f_padding]").val(g["f_padding"]);
    $("#editattachment INPUT[name=f_margin]").val(g["f_margin"]);
    $("#editattachment INPUT[name=f_width]").val(g["f_width"]);
    $("#editattachment INPUT[name=f_height]").val(g["f_height"]);
    $("#editattachment INPUT[name=f_bgcolor]").val(g["f_backgroundColor"]);
    $("#editattachment INPUT[name=f_bordercolor]").val(g["f_borderColor"]);

    $("#editattachment .preview").html('<img src="../_utils/thumbnail/'+fileName+'">');

    $("#editattachment").dialog('open');
};



