function UnsavedChanges(editor) {
    // Keep a copy of the editor to perform any necessary functions
    var editor = editor;

    // Private variable for storing the unmodified contents.  This is necessary
    // because whenDocReady needs a closure to reference this object.
    var defaultValue;

    // Variable to allow the protector to be bypassed in the case of submit.
    var bypass = false;

    var protector = function(event) {
        if (bypass) {
            return;
        }

        if (defaultValue != (editor.getEditorContent ? editor.getEditorContent() : editor.outwardHtml(editor.getHTML()))) {
            // This needs to use _lc for multiple languages
            var dirty_prompt = Xinha._lc('You have unsaved changes in the editor', 'UnsavedChanges');
            event.returnValue = dirty_prompt;
            return dirty_prompt;
        }
    }

    this.onBeforeSubmit = function() {
        bypass = true;
    }

    // Setup to be called when the plugin is loaded.
    // We need a copy of the initial content for detection to work properly, so
    // we will setup a callback for when the document is ready to store an
    // unmodified copy of the content.
    this.onGenerate = function() {
        editor.whenDocReady(function () {
            // Copy the original, unmodified contents to check for changes
            defaultValue = defaultValue || (editor.getEditorContent ? editor.getEditorContent() : editor.outwardHtml(editor.getHTML()));

            // Set up the blocker
            Xinha._addEvent(window, 'beforeunload', protector);
        });
    }

}

// An object containing metadata for this plugin
UnsavedChanges._pluginInfo = {
    name:'UnsavedChanges',
    version:'3.7',
    developer:'Douglas Mayle',
    developer_url:'http://douglas.mayle.org',
    c_owner:'Douglas Mayle',
    sponsor:'The Open Planning Project',
    sponsor_url:'http://topp.openplans.org',
    license:'LGPL'
}
