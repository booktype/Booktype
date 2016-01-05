//
// ice - v0.5.0
// The MIT License
// Copyright (c) 2012 The New York Times, CMS Group, Matthew DeLambo <delambo@gmail.com> 
//
window['rangy'] = (function() {


    var OBJECT = "object", FUNCTION = "function", UNDEFINED = "undefined";

    var domRangeProperties = ["startContainer", "startOffset", "endContainer", "endOffset", "collapsed",
        "commonAncestorContainer", "START_TO_START", "START_TO_END", "END_TO_START", "END_TO_END"];

    var domRangeMethods = ["setStart", "setStartBefore", "setStartAfter", "setEnd", "setEndBefore",
        "setEndAfter", "collapse", "selectNode", "selectNodeContents", "compareBoundaryPoints", "deleteContents",
        "extractContents", "cloneContents", "insertNode", "surroundContents", "cloneRange", "toString", "detach"];

    var textRangeProperties = ["boundingHeight", "boundingLeft", "boundingTop", "boundingWidth", "htmlText", "text"];

    // Subset of TextRange's full set of methods that we're interested in
    var textRangeMethods = ["collapse", "compareEndPoints", "duplicate", "getBookmark", "moveToBookmark",
        "moveToElementText", "parentElement", "pasteHTML", "select", "setEndPoint", "getBoundingClientRect"];

    /*----------------------------------------------------------------------------------------------------------------*/

    // Trio of functions taken from Peter Michaux's article:
    // http://peter.michaux.ca/articles/feature-detection-state-of-the-art-browser-scripting
    function isHostMethod(o, p) {
        var t = typeof o[p];
        return t == FUNCTION || (!!(t == OBJECT && o[p])) || t == "unknown";
    }

    function isHostObject(o, p) {
        return !!(typeof o[p] == OBJECT && o[p]);
    }

    function isHostProperty(o, p) {
        return typeof o[p] != UNDEFINED;
    }

    // Creates a convenience function to save verbose repeated calls to tests functions
    function createMultiplePropertyTest(testFunc) {
        return function(o, props) {
            var i = props.length;
            while (i--) {
                if (!testFunc(o, props[i])) {
                    return false;
                }
            }
            return true;
        };
    }

    // Next trio of functions are a convenience to save verbose repeated calls to previous two functions
    var areHostMethods = createMultiplePropertyTest(isHostMethod);
    var areHostObjects = createMultiplePropertyTest(isHostObject);
    var areHostProperties = createMultiplePropertyTest(isHostProperty);

    function isTextRange(range) {
        return range && areHostMethods(range, textRangeMethods) && areHostProperties(range, textRangeProperties);
    }

    var api = {
        version: "1.2.3",
        initialized: false,
        supported: true,

        util: {
            isHostMethod: isHostMethod,
            isHostObject: isHostObject,
            isHostProperty: isHostProperty,
            areHostMethods: areHostMethods,
            areHostObjects: areHostObjects,
            areHostProperties: areHostProperties,
            isTextRange: isTextRange
        },

        features: {},

        modules: {},
        config: {
            alertOnWarn: false,
            preferTextRange: false
        }
    };

    function fail(reason) {
        window.alert("Rangy not supported in your browser. Reason: " + reason);
        api.initialized = true;
        api.supported = false;
    }

    api.fail = fail;

    function warn(msg) {
        var warningMessage = "Rangy warning: " + msg;
        if (api.config.alertOnWarn) {
            window.alert(warningMessage);
        } else if (typeof window.console != UNDEFINED && typeof window.console.log != UNDEFINED) {
            window.console.log(warningMessage);
        }
    }

    api.warn = warn;

    if ({}.hasOwnProperty) {
        api.util.extend = function(o, props) {
            for (var i in props) {
                if (props.hasOwnProperty(i)) {
                    o[i] = props[i];
                }
            }
        };
    } else {
        fail("hasOwnProperty not supported");
    }

    var initListeners = [];
    var moduleInitializers = [];

    // Initialization
    function init() {
        if (api.initialized) {
            return;
        }
        var testRange;
        var implementsDomRange = false, implementsTextRange = false;

        // First, perform basic feature tests

        if (isHostMethod(document, "createRange")) {
            testRange = document.createRange();
            if (areHostMethods(testRange, domRangeMethods) && areHostProperties(testRange, domRangeProperties)) {
                implementsDomRange = true;
            }
            testRange.detach();
        }

        var body = isHostObject(document, "body") ? document.body : document.getElementsByTagName("body")[0];

        if (body && isHostMethod(body, "createTextRange")) {
            testRange = body.createTextRange();
            if (isTextRange(testRange)) {
                implementsTextRange = true;
            }
        }

        if (!implementsDomRange && !implementsTextRange) {
            fail("Neither Range nor TextRange are implemented");
        }

        api.initialized = true;
        api.features = {
            implementsDomRange: implementsDomRange,
            implementsTextRange: implementsTextRange
        };

        // Initialize modules and call init listeners
        var allListeners = moduleInitializers.concat(initListeners);
        for (var i = 0, len = allListeners.length; i < len; ++i) {
            try {
                allListeners[i](api);
            } catch (ex) {
                if (isHostObject(window, "console") && isHostMethod(window.console, "log")) {
                    window.console.log("Init listener threw an exception. Continuing.", ex);
                }

            }
        }
    }

    // Allow external scripts to initialize this library in case it's loaded after the document has loaded
    api.init = init;

    // Execute listener immediately if already initialized
    api.addInitListener = function(listener) {
        if (api.initialized) {
            listener(api);
        } else {
            initListeners.push(listener);
        }
    };

    var createMissingNativeApiListeners = [];

    api.addCreateMissingNativeApiListener = function(listener) {
        createMissingNativeApiListeners.push(listener);
    };

    function createMissingNativeApi(win) {
        win = win || window;
        init();

        // Notify listeners
        for (var i = 0, len = createMissingNativeApiListeners.length; i < len; ++i) {
            createMissingNativeApiListeners[i](win);
        }
    }

    api.createMissingNativeApi = createMissingNativeApi;

    /**
     * @constructor
     */
    function Module(name) {
        this.name = name;
        this.initialized = false;
        this.supported = false;
    }

    Module.prototype.fail = function(reason) {
        this.initialized = true;
        this.supported = false;

        throw new Error("Module '" + this.name + "' failed to load: " + reason);
    };

    Module.prototype.warn = function(msg) {
        api.warn("Module " + this.name + ": " + msg);
    };

    Module.prototype.createError = function(msg) {
        return new Error("Error in Rangy " + this.name + " module: " + msg);
    };

    api.createModule = function(name, initFunc) {
        var module = new Module(name);
        api.modules[name] = module;

        moduleInitializers.push(function(api) {
            initFunc(api, module);
            module.initialized = true;
            module.supported = true;
        });
    };

    api.requireModules = function(modules) {
        for (var i = 0, len = modules.length, module, moduleName; i < len; ++i) {
            moduleName = modules[i];
            module = api.modules[moduleName];
            if (!module || !(module instanceof Module)) {
                throw new Error("Module '" + moduleName + "' not found");
            }
            if (!module.supported) {
                throw new Error("Module '" + moduleName + "' not supported");
            }
        }
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    // Wait for document to load before running tests

    var docReady = false;

    var loadHandler = function(e) {

        if (!docReady) {
            docReady = true;
            if (!api.initialized) {
                init();
            }
        }
    };

    // Test whether we have window and document objects that we will need
    if (typeof window == UNDEFINED) {
        fail("No window found");
        return;
    }
    if (typeof document == UNDEFINED) {
        fail("No document found");
        return;
    }

    if (isHostMethod(document, "addEventListener")) {
        document.addEventListener("DOMContentLoaded", loadHandler, false);
    }

    // Add a fallback in case the DOMContentLoaded event isn't supported
    if (isHostMethod(window, "addEventListener")) {
        window.addEventListener("load", loadHandler, false);
    } else if (isHostMethod(window, "attachEvent")) {
        window.attachEvent("onload", loadHandler);
    } else {
        fail("Window does not have required addEventListener or attachEvent method");
    }

    return api;
})();
rangy.createModule("DomUtil", function(api, module) {

    var UNDEF = "undefined";
    var util = api.util;

    // Perform feature tests
    if (!util.areHostMethods(document, ["createDocumentFragment", "createElement", "createTextNode"])) {
        module.fail("document missing a Node creation method");
    }

    if (!util.isHostMethod(document, "getElementsByTagName")) {
        module.fail("document missing getElementsByTagName method");
    }

    var el = document.createElement("div");
    if (!util.areHostMethods(el, ["insertBefore", "appendChild", "cloneNode"] ||
            !util.areHostObjects(el, ["previousSibling", "nextSibling", "childNodes", "parentNode"]))) {
        module.fail("Incomplete Element implementation");
    }

    // innerHTML is required for Range's createContextualFragment method
    if (!util.isHostProperty(el, "innerHTML")) {
        module.fail("Element is missing innerHTML property");
    }

    var textNode = document.createTextNode("test");
    if (!util.areHostMethods(textNode, ["splitText", "deleteData", "insertData", "appendData", "cloneNode"] ||
            !util.areHostObjects(el, ["previousSibling", "nextSibling", "childNodes", "parentNode"]) ||
            !util.areHostProperties(textNode, ["data"]))) {
        module.fail("Incomplete Text Node implementation");
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Removed use of indexOf because of a bizarre bug in Opera that is thrown in one of the Acid3 tests. I haven't been
    // able to replicate it outside of the test. The bug is that indexOf returns -1 when called on an Array that
    // contains just the document as a single element and the value searched for is the document.
    var arrayContains = /*Array.prototype.indexOf ?
        function(arr, val) {
            return arr.indexOf(val) > -1;
        }:*/

        function(arr, val) {
            var i = arr.length;
            while (i--) {
                if (arr[i] === val) {
                    return true;
                }
            }
            return false;
        };

    // Opera 11 puts HTML elements in the null namespace, it seems, and IE 7 has undefined namespaceURI
    function isHtmlNamespace(node) {
        var ns;
        return typeof node.namespaceURI == UNDEF || ((ns = node.namespaceURI) === null || ns == "http://www.w3.org/1999/xhtml");
    }

    function parentElement(node) {
        var parent = node.parentNode;
        return (parent.nodeType == 1) ? parent : null;
    }

    function getNodeIndex(node) {
        var i = 0;
        while( (node = node.previousSibling) ) {
            i++;
        }
        return i;
    }

    function getNodeLength(node) {
        var childNodes;
        return isCharacterDataNode(node) ? node.length : ((childNodes = node.childNodes) ? childNodes.length : 0);
    }

    function getCommonAncestor(node1, node2) {
        var ancestors = [], n;
        for (n = node1; n; n = n.parentNode) {
            ancestors.push(n);
        }

        for (n = node2; n; n = n.parentNode) {
            if (arrayContains(ancestors, n)) {
                return n;
            }
        }

        return null;
    }

    function isAncestorOf(ancestor, descendant, selfIsAncestor) {
        var n = selfIsAncestor ? descendant : descendant.parentNode;
        while (n) {
            if (n === ancestor) {
                return true;
            } else {
                n = n.parentNode;
            }
        }
        return false;
    }

    function getClosestAncestorIn(node, ancestor, selfIsAncestor) {
        var p, n = selfIsAncestor ? node : node.parentNode;
        while (n) {
            p = n.parentNode;
            if (p === ancestor) {
                return n;
            }
            n = p;
        }
        return null;
    }

    function isCharacterDataNode(node) {
        var t = node.nodeType;
        return t == 3 || t == 4 || t == 8 ; // Text, CDataSection or Comment
    }

    function insertAfter(node, precedingNode) {
        var nextNode = precedingNode.nextSibling, parent = precedingNode.parentNode;
        if (nextNode) {
            parent.insertBefore(node, nextNode);
        } else {
            parent.appendChild(node);
        }
        return node;
    }

    // Note that we cannot use splitText() because it is bugridden in IE 9.
    function splitDataNode(node, index) {
        var newNode = node.cloneNode(false);
        newNode.deleteData(0, index);
        node.deleteData(index, node.length - index);
        insertAfter(newNode, node);
        return newNode;
    }

    function getDocument(node) {
        if (node.nodeType == 9) {
            return node;
        } else if (typeof node.ownerDocument != UNDEF) {
            return node.ownerDocument;
        } else if (typeof node.document != UNDEF) {
            return node.document;
        } else if (node.parentNode) {
            return getDocument(node.parentNode);
        } else {
            throw new Error("getDocument: no document found for node");
        }
    }

    function getWindow(node) {
        var doc = getDocument(node);
        if (typeof doc.defaultView != UNDEF) {
            return doc.defaultView;
        } else if (typeof doc.parentWindow != UNDEF) {
            return doc.parentWindow;
        } else {
            throw new Error("Cannot get a window object for node");
        }
    }

    function getIframeDocument(iframeEl) {
        if (typeof iframeEl.contentDocument != UNDEF) {
            return iframeEl.contentDocument;
        } else if (typeof iframeEl.contentWindow != UNDEF) {
            return iframeEl.contentWindow.document;
        } else {
            throw new Error("getIframeWindow: No Document object found for iframe element");
        }
    }

    function getIframeWindow(iframeEl) {
        if (typeof iframeEl.contentWindow != UNDEF) {
            return iframeEl.contentWindow;
        } else if (typeof iframeEl.contentDocument != UNDEF) {
            return iframeEl.contentDocument.defaultView;
        } else {
            throw new Error("getIframeWindow: No Window object found for iframe element");
        }
    }

    function getBody(doc) {
        return util.isHostObject(doc, "body") ? doc.body : doc.getElementsByTagName("body")[0];
    }

    function getRootContainer(node) {
        var parent;
        while ( (parent = node.parentNode) ) {
            node = parent;
        }
        return node;
    }

    function comparePoints(nodeA, offsetA, nodeB, offsetB) {
        // See http://www.w3.org/TR/DOM-Level-2-Traversal-Range/ranges.html#Level-2-Range-Comparing
        var nodeC, root, childA, childB, n;
        if (nodeA == nodeB) {

            // Case 1: nodes are the same
            return offsetA === offsetB ? 0 : (offsetA < offsetB) ? -1 : 1;
        } else if ( (nodeC = getClosestAncestorIn(nodeB, nodeA, true)) ) {

            // Case 2: node C (container B or an ancestor) is a child node of A
            return offsetA <= getNodeIndex(nodeC) ? -1 : 1;
        } else if ( (nodeC = getClosestAncestorIn(nodeA, nodeB, true)) ) {

            // Case 3: node C (container A or an ancestor) is a child node of B
            return getNodeIndex(nodeC) < offsetB  ? -1 : 1;
        } else {

            // Case 4: containers are siblings or descendants of siblings
            root = getCommonAncestor(nodeA, nodeB);
            childA = (nodeA === root) ? root : getClosestAncestorIn(nodeA, root, true);
            childB = (nodeB === root) ? root : getClosestAncestorIn(nodeB, root, true);

            if (childA === childB) {
                // This shouldn't be possible

                throw new Error("comparePoints got to case 4 and childA and childB are the same!");
            } else {
                n = root.firstChild;
                while (n) {
                    if (n === childA) {
                        return -1;
                    } else if (n === childB) {
                        return 1;
                    }
                    n = n.nextSibling;
                }
                throw new Error("Should not be here!");
            }
        }
    }

    function fragmentFromNodeChildren(node) {
        var fragment = getDocument(node).createDocumentFragment(), child;
        while ( (child = node.firstChild) ) {
            fragment.appendChild(child);
        }
        return fragment;
    }

    function inspectNode(node) {
        if (!node) {
            return "[No node]";
        }
        if (isCharacterDataNode(node)) {
            return '"' + node.data + '"';
        } else if (node.nodeType == 1) {
            var idAttr = node.id ? ' id="' + node.id + '"' : "";
            return "<" + node.nodeName + idAttr + ">[" + node.childNodes.length + "]";
        } else {
            return node.nodeName;
        }
    }

    /**
     * @constructor
     */
    function NodeIterator(root) {
        this.root = root;
        this._next = root;
    }

    NodeIterator.prototype = {
        _current: null,

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            var n = this._current = this._next;
            var child, next;
            if (this._current) {
                child = n.firstChild;
                if (child) {
                    this._next = child;
                } else {
                    next = null;
                    while ((n !== this.root) && !(next = n.nextSibling)) {
                        n = n.parentNode;
                    }
                    this._next = next;
                }
            }
            return this._current;
        },

        detach: function() {
            this._current = this._next = this.root = null;
        }
    };

    function createIterator(root) {
        return new NodeIterator(root);
    }

    /**
     * @constructor
     */
    function DomPosition(node, offset) {
        this.node = node;
        this.offset = offset;
    }

    DomPosition.prototype = {
        equals: function(pos) {
            return this.node === pos.node & this.offset == pos.offset;
        },

        inspect: function() {
            return "[DomPosition(" + inspectNode(this.node) + ":" + this.offset + ")]";
        }
    };

    /**
     * @constructor
     */
    function DOMException(codeName) {
        this.code = this[codeName];
        this.codeName = codeName;
        this.message = "DOMException: " + this.codeName;
    }

    DOMException.prototype = {
        INDEX_SIZE_ERR: 1,
        HIERARCHY_REQUEST_ERR: 3,
        WRONG_DOCUMENT_ERR: 4,
        NO_MODIFICATION_ALLOWED_ERR: 7,
        NOT_FOUND_ERR: 8,
        NOT_SUPPORTED_ERR: 9,
        INVALID_STATE_ERR: 11
    };

    DOMException.prototype.toString = function() {
        return this.message;
    };

    api.dom = {
        arrayContains: arrayContains,
        isHtmlNamespace: isHtmlNamespace,
        parentElement: parentElement,
        getNodeIndex: getNodeIndex,
        getNodeLength: getNodeLength,
        getCommonAncestor: getCommonAncestor,
        isAncestorOf: isAncestorOf,
        getClosestAncestorIn: getClosestAncestorIn,
        isCharacterDataNode: isCharacterDataNode,
        insertAfter: insertAfter,
        splitDataNode: splitDataNode,
        getDocument: getDocument,
        getWindow: getWindow,
        getIframeWindow: getIframeWindow,
        getIframeDocument: getIframeDocument,
        getBody: getBody,
        getRootContainer: getRootContainer,
        comparePoints: comparePoints,
        inspectNode: inspectNode,
        fragmentFromNodeChildren: fragmentFromNodeChildren,
        createIterator: createIterator,
        DomPosition: DomPosition
    };

    api.DOMException = DOMException;
});rangy.createModule("DomRange", function(api, module) {
    api.requireModules( ["DomUtil"] );


    var dom = api.dom;
    var DomPosition = dom.DomPosition;
    var DOMException = api.DOMException;
    
    /*----------------------------------------------------------------------------------------------------------------*/

    // Utility functions

    function isNonTextPartiallySelected(node, range) {
        return (node.nodeType != 3) &&
               (dom.isAncestorOf(node, range.startContainer, true) || dom.isAncestorOf(node, range.endContainer, true));
    }

    function getRangeDocument(range) {
        return dom.getDocument(range.startContainer);
    }

    function dispatchEvent(range, type, args) {
        var listeners = range._listeners[type];
        if (listeners) {
            for (var i = 0, len = listeners.length; i < len; ++i) {
                listeners[i].call(range, {target: range, args: args});
            }
        }
    }

    function getBoundaryBeforeNode(node) {
        return new DomPosition(node.parentNode, dom.getNodeIndex(node));
    }

    function getBoundaryAfterNode(node) {
        return new DomPosition(node.parentNode, dom.getNodeIndex(node) + 1);
    }

    function insertNodeAtPosition(node, n, o) {
        var firstNodeInserted = node.nodeType == 11 ? node.firstChild : node;
        if (dom.isCharacterDataNode(n)) {
            if (o == n.length) {
                dom.insertAfter(node, n);
            } else {
                n.parentNode.insertBefore(node, o == 0 ? n : dom.splitDataNode(n, o));
            }
        } else if (o >= n.childNodes.length) {
            n.appendChild(node);
        } else {
            n.insertBefore(node, n.childNodes[o]);
        }
        return firstNodeInserted;
    }

    function cloneSubtree(iterator) {
        var partiallySelected;
        for (var node, frag = getRangeDocument(iterator.range).createDocumentFragment(), subIterator; node = iterator.next(); ) {
            partiallySelected = iterator.isPartiallySelectedSubtree();

            node = node.cloneNode(!partiallySelected);
            if (partiallySelected) {
                subIterator = iterator.getSubtreeIterator();
                node.appendChild(cloneSubtree(subIterator));
                subIterator.detach(true);
            }

            if (node.nodeType == 10) { // DocumentType
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }
            frag.appendChild(node);
        }
        return frag;
    }

    function iterateSubtree(rangeIterator, func, iteratorState) {
        var it, n;
        iteratorState = iteratorState || { stop: false };
        for (var node, subRangeIterator; node = rangeIterator.next(); ) {
            //log.debug("iterateSubtree, partially selected: " + rangeIterator.isPartiallySelectedSubtree(), nodeToString(node));
            if (rangeIterator.isPartiallySelectedSubtree()) {
                // The node is partially selected by the Range, so we can use a new RangeIterator on the portion of the
                // node selected by the Range.
                if (func(node) === false) {
                    iteratorState.stop = true;
                    return;
                } else {
                    subRangeIterator = rangeIterator.getSubtreeIterator();
                    iterateSubtree(subRangeIterator, func, iteratorState);
                    subRangeIterator.detach(true);
                    if (iteratorState.stop) {
                        return;
                    }
                }
            } else {
                // The whole node is selected, so we can use efficient DOM iteration to iterate over the node and its
                // descendant
                it = dom.createIterator(node);
                while ( (n = it.next()) ) {
                    if (func(n) === false) {
                        iteratorState.stop = true;
                        return;
                    }
                }
            }
        }
    }

    function deleteSubtree(iterator) {
        var subIterator;
        while (iterator.next()) {
            if (iterator.isPartiallySelectedSubtree()) {
                subIterator = iterator.getSubtreeIterator();
                deleteSubtree(subIterator);
                subIterator.detach(true);
            } else {
                iterator.remove();
            }
        }
    }

    function extractSubtree(iterator) {

        for (var node, frag = getRangeDocument(iterator.range).createDocumentFragment(), subIterator; node = iterator.next(); ) {


            if (iterator.isPartiallySelectedSubtree()) {
                node = node.cloneNode(false);
                subIterator = iterator.getSubtreeIterator();
                node.appendChild(extractSubtree(subIterator));
                subIterator.detach(true);
            } else {
                iterator.remove();
            }
            if (node.nodeType == 10) { // DocumentType
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }
            frag.appendChild(node);
        }
        return frag;
    }

    function getNodesInRange(range, nodeTypes, filter) {
        //log.info("getNodesInRange, " + nodeTypes.join(","));
        var filterNodeTypes = !!(nodeTypes && nodeTypes.length), regex;
        var filterExists = !!filter;
        if (filterNodeTypes) {
            regex = new RegExp("^(" + nodeTypes.join("|") + ")$");
        }

        var nodes = [];
        iterateSubtree(new RangeIterator(range, false), function(node) {
            if ((!filterNodeTypes || regex.test(node.nodeType)) && (!filterExists || filter(node))) {
                nodes.push(node);
            }
        });
        return nodes;
    }

    function inspect(range) {
        var name = (typeof range.getName == "undefined") ? "Range" : range.getName();
        return "[" + name + "(" + dom.inspectNode(range.startContainer) + ":" + range.startOffset + ", " +
                dom.inspectNode(range.endContainer) + ":" + range.endOffset + ")]";
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // RangeIterator code partially borrows from IERange by Tim Ryan (http://github.com/timcameronryan/IERange)

    /**
     * @constructor
     */
    function RangeIterator(range, clonePartiallySelectedTextNodes) {
        this.range = range;
        this.clonePartiallySelectedTextNodes = clonePartiallySelectedTextNodes;



        if (!range.collapsed) {
            this.sc = range.startContainer;
            this.so = range.startOffset;
            this.ec = range.endContainer;
            this.eo = range.endOffset;
            var root = range.commonAncestorContainer;

            if (this.sc === this.ec && dom.isCharacterDataNode(this.sc)) {
                this.isSingleCharacterDataNode = true;
                this._first = this._last = this._next = this.sc;
            } else {
                this._first = this._next = (this.sc === root && !dom.isCharacterDataNode(this.sc)) ?
                    this.sc.childNodes[this.so] : dom.getClosestAncestorIn(this.sc, root, true);
                this._last = (this.ec === root && !dom.isCharacterDataNode(this.ec)) ?
                    this.ec.childNodes[this.eo - 1] : dom.getClosestAncestorIn(this.ec, root, true);
            }

        }
    }

    RangeIterator.prototype = {
        _current: null,
        _next: null,
        _first: null,
        _last: null,
        isSingleCharacterDataNode: false,

        reset: function() {
            this._current = null;
            this._next = this._first;
        },

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            // Move to next node
            var current = this._current = this._next;
            if (current) {
                this._next = (current !== this._last) ? current.nextSibling : null;

                // Check for partially selected text nodes
                if (dom.isCharacterDataNode(current) && this.clonePartiallySelectedTextNodes) {
                    if (current === this.ec) {

                        (current = current.cloneNode(true)).deleteData(this.eo, current.length - this.eo);
                    }
                    if (this._current === this.sc) {

                        (current = current.cloneNode(true)).deleteData(0, this.so);
                    }
                }
            }

            return current;
        },

        remove: function() {
            var current = this._current, start, end;

            if (dom.isCharacterDataNode(current) && (current === this.sc || current === this.ec)) {
                start = (current === this.sc) ? this.so : 0;
                end = (current === this.ec) ? this.eo : current.length;
                if (start != end) {
                    current.deleteData(start, end - start);
                }
            } else {
                if (current.parentNode) {
                    current.parentNode.removeChild(current);
                } else {

                }
            }
        },

        // Checks if the current node is partially selected
        isPartiallySelectedSubtree: function() {
            var current = this._current;
            return isNonTextPartiallySelected(current, this.range);
        },

        getSubtreeIterator: function() {
            var subRange;
            if (this.isSingleCharacterDataNode) {
                subRange = this.range.cloneRange();
                subRange.collapse();
            } else {
                subRange = new Range(getRangeDocument(this.range));
                var current = this._current;
                var startContainer = current, startOffset = 0, endContainer = current, endOffset = dom.getNodeLength(current);

                if (dom.isAncestorOf(current, this.sc, true)) {
                    startContainer = this.sc;
                    startOffset = this.so;
                }
                if (dom.isAncestorOf(current, this.ec, true)) {
                    endContainer = this.ec;
                    endOffset = this.eo;
                }

                updateBoundaries(subRange, startContainer, startOffset, endContainer, endOffset);
            }
            return new RangeIterator(subRange, this.clonePartiallySelectedTextNodes);
        },

        detach: function(detachRange) {
            if (detachRange) {
                this.range.detach();
            }
            this.range = this._current = this._next = this._first = this._last = this.sc = this.so = this.ec = this.eo = null;
        }
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    // Exceptions

    /**
     * @constructor
     */
    function RangeException(codeName) {
        this.code = this[codeName];
        this.codeName = codeName;
        this.message = "RangeException: " + this.codeName;
    }

    RangeException.prototype = {
        BAD_BOUNDARYPOINTS_ERR: 1,
        INVALID_NODE_TYPE_ERR: 2
    };

    RangeException.prototype.toString = function() {
        return this.message;
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    /**
     * Currently iterates through all nodes in the range on creation until I think of a decent way to do it
     * TODO: Look into making this a proper iterator, not requiring preloading everything first
     * @constructor
     */
    function RangeNodeIterator(range, nodeTypes, filter) {
        this.nodes = getNodesInRange(range, nodeTypes, filter);
        this._next = this.nodes[0];
        this._position = 0;
    }

    RangeNodeIterator.prototype = {
        _current: null,

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            this._current = this._next;
            this._next = this.nodes[ ++this._position ];
            return this._current;
        },

        detach: function() {
            this._current = this._next = this.nodes = null;
        }
    };

    var beforeAfterNodeTypes = [1, 3, 4, 5, 7, 8, 10];
    var rootContainerNodeTypes = [2, 9, 11];
    var readonlyNodeTypes = [5, 6, 10, 12];
    var insertableNodeTypes = [1, 3, 4, 5, 7, 8, 10, 11];
    var surroundNodeTypes = [1, 3, 4, 5, 7, 8];

    function createAncestorFinder(nodeTypes) {
        return function(node, selfIsAncestor) {
            var t, n = selfIsAncestor ? node : node.parentNode;
            while (n) {
                t = n.nodeType;
                if (dom.arrayContains(nodeTypes, t)) {
                    return n;
                }
                n = n.parentNode;
            }
            return null;
        };
    }

    var getRootContainer = dom.getRootContainer;
    var getDocumentOrFragmentContainer = createAncestorFinder( [9, 11] );
    var getReadonlyAncestor = createAncestorFinder(readonlyNodeTypes);
    var getDocTypeNotationEntityAncestor = createAncestorFinder( [6, 10, 12] );

    function assertNoDocTypeNotationEntityAncestor(node, allowSelf) {
        if (getDocTypeNotationEntityAncestor(node, allowSelf)) {
            throw new RangeException("INVALID_NODE_TYPE_ERR");
        }
    }

    function assertNotDetached(range) {
        if (!range.startContainer) {
            throw new DOMException("INVALID_STATE_ERR");
        }
    }

    function assertValidNodeType(node, invalidTypes) {
        if (!dom.arrayContains(invalidTypes, node.nodeType)) {
            throw new RangeException("INVALID_NODE_TYPE_ERR");
        }
    }

    function assertValidOffset(node, offset) {
        if (offset < 0 || offset > (dom.isCharacterDataNode(node) ? node.length : node.childNodes.length)) {
            throw new DOMException("INDEX_SIZE_ERR");
        }
    }

    function assertSameDocumentOrFragment(node1, node2) {
        if (getDocumentOrFragmentContainer(node1, true) !== getDocumentOrFragmentContainer(node2, true)) {
            throw new DOMException("WRONG_DOCUMENT_ERR");
        }
    }

    function assertNodeNotReadOnly(node) {
        if (getReadonlyAncestor(node, true)) {
            throw new DOMException("NO_MODIFICATION_ALLOWED_ERR");
        }
    }

    function assertNode(node, codeName) {
        if (!node) {
            throw new DOMException(codeName);
        }
    }

    function isOrphan(node) {
        return !dom.arrayContains(rootContainerNodeTypes, node.nodeType) && !getDocumentOrFragmentContainer(node, true);
    }

    function isValidOffset(node, offset) {
        return offset <= (dom.isCharacterDataNode(node) ? node.length : node.childNodes.length);
    }

    function isRangeValid(range) {
        return (!!range.startContainer && !!range.endContainer
                && !isOrphan(range.startContainer)
                && !isOrphan(range.endContainer)
                && isValidOffset(range.startContainer, range.startOffset)
                && isValidOffset(range.endContainer, range.endOffset));
    }

    function assertRangeValid(range) {
        assertNotDetached(range);
        if (!isRangeValid(range)) {
            throw new Error("Range error: Range is no longer valid after DOM mutation (" + range.inspect() + ")");
        }
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Test the browser's innerHTML support to decide how to implement createContextualFragment
    var styleEl = document.createElement("style");
    var htmlParsingConforms = false;
    try {
        styleEl.innerHTML = "<b>x</b>";
        htmlParsingConforms = (styleEl.firstChild.nodeType == 3); // Opera incorrectly creates an element node
    } catch (e) {
        // IE 6 and 7 throw
    }

    api.features.htmlParsingConforms = htmlParsingConforms;

    var createContextualFragment = htmlParsingConforms ?

        // Implementation as per HTML parsing spec, trusting in the browser's implementation of innerHTML. See
        // discussion and base code for this implementation at issue 67.
        // Spec: http://html5.org/specs/dom-parsing.html#extensions-to-the-range-interface
        // Thanks to Aleks Williams.
        function(fragmentStr) {
            // "Let node the context object's start's node."
            var node = this.startContainer;
            var doc = dom.getDocument(node);

            // "If the context object's start's node is null, raise an INVALID_STATE_ERR
            // exception and abort these steps."
            if (!node) {
                throw new DOMException("INVALID_STATE_ERR");
            }

            // "Let element be as follows, depending on node's interface:"
            // Document, Document Fragment: null
            var el = null;

            // "Element: node"
            if (node.nodeType == 1) {
                el = node;

            // "Text, Comment: node's parentElement"
            } else if (dom.isCharacterDataNode(node)) {
                el = dom.parentElement(node);
            }

            // "If either element is null or element's ownerDocument is an HTML document
            // and element's local name is "html" and element's namespace is the HTML
            // namespace"
            if (el === null || (
                el.nodeName == "HTML"
                && dom.isHtmlNamespace(dom.getDocument(el).documentElement)
                && dom.isHtmlNamespace(el)
            )) {

            // "let element be a new Element with "body" as its local name and the HTML
            // namespace as its namespace.""
                el = doc.createElement("body");
            } else {
                el = el.cloneNode(false);
            }

            // "If the node's document is an HTML document: Invoke the HTML fragment parsing algorithm."
            // "If the node's document is an XML document: Invoke the XML fragment parsing algorithm."
            // "In either case, the algorithm must be invoked with fragment as the input
            // and element as the context element."
            el.innerHTML = fragmentStr;

            // "If this raises an exception, then abort these steps. Otherwise, let new
            // children be the nodes returned."

            // "Let fragment be a new DocumentFragment."
            // "Append all new children to fragment."
            // "Return fragment."
            return dom.fragmentFromNodeChildren(el);
        } :

        // In this case, innerHTML cannot be trusted, so fall back to a simpler, non-conformant implementation that
        // previous versions of Rangy used (with the exception of using a body element rather than a div)
        function(fragmentStr) {
            assertNotDetached(this);
            var doc = getRangeDocument(this);
            var el = doc.createElement("body");
            el.innerHTML = fragmentStr;

            return dom.fragmentFromNodeChildren(el);
        };

    /*----------------------------------------------------------------------------------------------------------------*/

    var rangeProperties = ["startContainer", "startOffset", "endContainer", "endOffset", "collapsed",
        "commonAncestorContainer"];

    var s2s = 0, s2e = 1, e2e = 2, e2s = 3;
    var n_b = 0, n_a = 1, n_b_a = 2, n_i = 3;

    function RangePrototype() {}

    RangePrototype.prototype = {
        attachListener: function(type, listener) {
            this._listeners[type].push(listener);
        },

        compareBoundaryPoints: function(how, range) {
            assertRangeValid(this);
            assertSameDocumentOrFragment(this.startContainer, range.startContainer);

            var nodeA, offsetA, nodeB, offsetB;
            var prefixA = (how == e2s || how == s2s) ? "start" : "end";
            var prefixB = (how == s2e || how == s2s) ? "start" : "end";
            nodeA = this[prefixA + "Container"];
            offsetA = this[prefixA + "Offset"];
            nodeB = range[prefixB + "Container"];
            offsetB = range[prefixB + "Offset"];
            return dom.comparePoints(nodeA, offsetA, nodeB, offsetB);
        },

        insertNode: function(node) {
            assertRangeValid(this);
            assertValidNodeType(node, insertableNodeTypes);
            assertNodeNotReadOnly(this.startContainer);

            if (dom.isAncestorOf(node, this.startContainer, true)) {
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }

            // No check for whether the container of the start of the Range is of a type that does not allow
            // children of the type of node: the browser's DOM implementation should do this for us when we attempt
            // to add the node

            var firstNodeInserted = insertNodeAtPosition(node, this.startContainer, this.startOffset);
            this.setStartBefore(firstNodeInserted);
        },

        cloneContents: function() {
            assertRangeValid(this);

            var clone, frag;
            if (this.collapsed) {
                return getRangeDocument(this).createDocumentFragment();
            } else {
                if (this.startContainer === this.endContainer && dom.isCharacterDataNode(this.startContainer)) {
                    clone = this.startContainer.cloneNode(true);
                    clone.data = clone.data.slice(this.startOffset, this.endOffset);
                    frag = getRangeDocument(this).createDocumentFragment();
                    frag.appendChild(clone);
                    return frag;
                } else {
                    var iterator = new RangeIterator(this, true);
                    clone = cloneSubtree(iterator);
                    iterator.detach();
                }
                return clone;
            }
        },

        canSurroundContents: function() {
            assertRangeValid(this);
            assertNodeNotReadOnly(this.startContainer);
            assertNodeNotReadOnly(this.endContainer);

            // Check if the contents can be surrounded. Specifically, this means whether the range partially selects
            // no non-text nodes.
            var iterator = new RangeIterator(this, true);
            var boundariesInvalid = (iterator._first && (isNonTextPartiallySelected(iterator._first, this)) ||
                    (iterator._last && isNonTextPartiallySelected(iterator._last, this)));
            iterator.detach();
            return !boundariesInvalid;
        },

        surroundContents: function(node) {
            assertValidNodeType(node, surroundNodeTypes);

            if (!this.canSurroundContents()) {
                throw new RangeException("BAD_BOUNDARYPOINTS_ERR");
            }

            // Extract the contents
            var content = this.extractContents();

            // Clear the children of the node
            if (node.hasChildNodes()) {
                while (node.lastChild) {
                    node.removeChild(node.lastChild);
                }
            }

            // Insert the new node and add the extracted contents
            insertNodeAtPosition(node, this.startContainer, this.startOffset);
            node.appendChild(content);

            this.selectNode(node);
        },

        cloneRange: function() {
            assertRangeValid(this);
            var range = new Range(getRangeDocument(this));
            var i = rangeProperties.length, prop;
            while (i--) {
                prop = rangeProperties[i];
                range[prop] = this[prop];
            }
            return range;
        },

        toString: function() {
            assertRangeValid(this);
            var sc = this.startContainer;
            if (sc === this.endContainer && dom.isCharacterDataNode(sc)) {
                return (sc.nodeType == 3 || sc.nodeType == 4) ? sc.data.slice(this.startOffset, this.endOffset) : "";
            } else {
                var textBits = [], iterator = new RangeIterator(this, true);

                iterateSubtree(iterator, function(node) {
                    // Accept only text or CDATA nodes, not comments

                    if (node.nodeType == 3 || node.nodeType == 4) {
                        textBits.push(node.data);
                    }
                });
                iterator.detach();
                return textBits.join("");
            }
        },

        // The methods below are all non-standard. The following batch were introduced by Mozilla but have since
        // been removed from Mozilla.

        compareNode: function(node) {
            assertRangeValid(this);

            var parent = node.parentNode;
            var nodeIndex = dom.getNodeIndex(node);

            if (!parent) {
                throw new DOMException("NOT_FOUND_ERR");
            }

            var startComparison = this.comparePoint(parent, nodeIndex),
                endComparison = this.comparePoint(parent, nodeIndex + 1);

            if (startComparison < 0) { // Node starts before
                return (endComparison > 0) ? n_b_a : n_b;
            } else {
                return (endComparison > 0) ? n_a : n_i;
            }
        },

        comparePoint: function(node, offset) {
            assertRangeValid(this);
            assertNode(node, "HIERARCHY_REQUEST_ERR");
            assertSameDocumentOrFragment(node, this.startContainer);

            if (dom.comparePoints(node, offset, this.startContainer, this.startOffset) < 0) {
                return -1;
            } else if (dom.comparePoints(node, offset, this.endContainer, this.endOffset) > 0) {
                return 1;
            }
            return 0;
        },

        createContextualFragment: createContextualFragment,

        toHtml: function() {
            assertRangeValid(this);
            var container = getRangeDocument(this).createElement("div");
            container.appendChild(this.cloneContents());
            return container.innerHTML;
        },

        // touchingIsIntersecting determines whether this method considers a node that borders a range intersects
        // with it (as in WebKit) or not (as in Gecko pre-1.9, and the default)
        intersectsNode: function(node, touchingIsIntersecting) {
            assertRangeValid(this);
            assertNode(node, "NOT_FOUND_ERR");
            if (dom.getDocument(node) !== getRangeDocument(this)) {
                return false;
            }

            var parent = node.parentNode, offset = dom.getNodeIndex(node);
            assertNode(parent, "NOT_FOUND_ERR");

            var startComparison = dom.comparePoints(parent, offset, this.endContainer, this.endOffset),
                endComparison = dom.comparePoints(parent, offset + 1, this.startContainer, this.startOffset);

            return touchingIsIntersecting ? startComparison <= 0 && endComparison >= 0 : startComparison < 0 && endComparison > 0;
        },


        isPointInRange: function(node, offset) {
            assertRangeValid(this);
            assertNode(node, "HIERARCHY_REQUEST_ERR");
            assertSameDocumentOrFragment(node, this.startContainer);

            return (dom.comparePoints(node, offset, this.startContainer, this.startOffset) >= 0) &&
                   (dom.comparePoints(node, offset, this.endContainer, this.endOffset) <= 0);
        },

        // The methods below are non-standard and invented by me.

        // Sharing a boundary start-to-end or end-to-start does not count as intersection.
        intersectsRange: function(range, touchingIsIntersecting) {
            assertRangeValid(this);

            if (getRangeDocument(range) != getRangeDocument(this)) {
                throw new DOMException("WRONG_DOCUMENT_ERR");
            }

            var startComparison = dom.comparePoints(this.startContainer, this.startOffset, range.endContainer, range.endOffset),
                endComparison = dom.comparePoints(this.endContainer, this.endOffset, range.startContainer, range.startOffset);

            return touchingIsIntersecting ? startComparison <= 0 && endComparison >= 0 : startComparison < 0 && endComparison > 0;
        },

        intersection: function(range) {
            if (this.intersectsRange(range)) {
                var startComparison = dom.comparePoints(this.startContainer, this.startOffset, range.startContainer, range.startOffset),
                    endComparison = dom.comparePoints(this.endContainer, this.endOffset, range.endContainer, range.endOffset);

                var intersectionRange = this.cloneRange();

                if (startComparison == -1) {
                    intersectionRange.setStart(range.startContainer, range.startOffset);
                }
                if (endComparison == 1) {
                    intersectionRange.setEnd(range.endContainer, range.endOffset);
                }
                return intersectionRange;
            }
            return null;
        },

        union: function(range) {
            if (this.intersectsRange(range, true)) {
                var unionRange = this.cloneRange();
                if (dom.comparePoints(range.startContainer, range.startOffset, this.startContainer, this.startOffset) == -1) {
                    unionRange.setStart(range.startContainer, range.startOffset);
                }
                if (dom.comparePoints(range.endContainer, range.endOffset, this.endContainer, this.endOffset) == 1) {
                    unionRange.setEnd(range.endContainer, range.endOffset);
                }
                return unionRange;
            } else {
                throw new RangeException("Ranges do not intersect");
            }
        },

        containsNode: function(node, allowPartial) {
            if (allowPartial) {
                return this.intersectsNode(node, false);
            } else {
                return this.compareNode(node) == n_i;
            }
        },

        containsNodeContents: function(node) {
            return this.comparePoint(node, 0) >= 0 && this.comparePoint(node, dom.getNodeLength(node)) <= 0;
        },

        containsRange: function(range) {
            return this.intersection(range).equals(range);
        },

        containsNodeText: function(node) {
            var nodeRange = this.cloneRange();
            nodeRange.selectNode(node);
            var textNodes = nodeRange.getNodes([3]);
            if (textNodes.length > 0) {
                nodeRange.setStart(textNodes[0], 0);
                var lastTextNode = textNodes.pop();
                nodeRange.setEnd(lastTextNode, lastTextNode.length);
                var contains = this.containsRange(nodeRange);
                nodeRange.detach();
                return contains;
            } else {
                return this.containsNodeContents(node);
            }
        },

        createNodeIterator: function(nodeTypes, filter) {
            assertRangeValid(this);
            return new RangeNodeIterator(this, nodeTypes, filter);
        },

        getNodes: function(nodeTypes, filter) {
            assertRangeValid(this);
            return getNodesInRange(this, nodeTypes, filter);
        },

        getDocument: function() {
            return getRangeDocument(this);
        },

        collapseBefore: function(node) {
            assertNotDetached(this);

            this.setEndBefore(node);
            this.collapse(false);
        },

        collapseAfter: function(node) {
            assertNotDetached(this);

            this.setStartAfter(node);
            this.collapse(true);
        },

        getName: function() {
            return "DomRange";
        },

        equals: function(range) {
            return Range.rangesEqual(this, range);
        },

        isValid: function() {
            return isRangeValid(this);
        },

        inspect: function() {
            return inspect(this);
        }
    };

    function copyComparisonConstantsToObject(obj) {
        obj.START_TO_START = s2s;
        obj.START_TO_END = s2e;
        obj.END_TO_END = e2e;
        obj.END_TO_START = e2s;

        obj.NODE_BEFORE = n_b;
        obj.NODE_AFTER = n_a;
        obj.NODE_BEFORE_AND_AFTER = n_b_a;
        obj.NODE_INSIDE = n_i;
    }

    function copyComparisonConstants(constructor) {
        copyComparisonConstantsToObject(constructor);
        copyComparisonConstantsToObject(constructor.prototype);
    }

    function createRangeContentRemover(remover, boundaryUpdater) {
        return function() {
            assertRangeValid(this);

            var sc = this.startContainer, so = this.startOffset, root = this.commonAncestorContainer;

            var iterator = new RangeIterator(this, true);

            // Work out where to position the range after content removal
            var node, boundary;
            if (sc !== root) {
                node = dom.getClosestAncestorIn(sc, root, true);
                boundary = getBoundaryAfterNode(node);
                sc = boundary.node;
                so = boundary.offset;
            }

            // Check none of the range is read-only
            iterateSubtree(iterator, assertNodeNotReadOnly);

            iterator.reset();

            // Remove the content
            var returnValue = remover(iterator);
            iterator.detach();

            // Move to the new position
            boundaryUpdater(this, sc, so, sc, so);

            return returnValue;
        };
    }

    function createPrototypeRange(constructor, boundaryUpdater, detacher) {
        function createBeforeAfterNodeSetter(isBefore, isStart) {
            return function(node) {
                assertNotDetached(this);
                assertValidNodeType(node, beforeAfterNodeTypes);
                assertValidNodeType(getRootContainer(node), rootContainerNodeTypes);

                var boundary = (isBefore ? getBoundaryBeforeNode : getBoundaryAfterNode)(node);
                (isStart ? setRangeStart : setRangeEnd)(this, boundary.node, boundary.offset);
            };
        }

        function setRangeStart(range, node, offset) {
            var ec = range.endContainer, eo = range.endOffset;
            if (node !== range.startContainer || offset !== range.startOffset) {
                // Check the root containers of the range and the new boundary, and also check whether the new boundary
                // is after the current end. In either case, collapse the range to the new position
                if (getRootContainer(node) != getRootContainer(ec) || dom.comparePoints(node, offset, ec, eo) == 1) {
                    ec = node;
                    eo = offset;
                }
                boundaryUpdater(range, node, offset, ec, eo);
            }
        }

        function setRangeEnd(range, node, offset) {
            var sc = range.startContainer, so = range.startOffset;
            if (node !== range.endContainer || offset !== range.endOffset) {
                // Check the root containers of the range and the new boundary, and also check whether the new boundary
                // is after the current end. In either case, collapse the range to the new position
                if (getRootContainer(node) != getRootContainer(sc) || dom.comparePoints(node, offset, sc, so) == -1) {
                    sc = node;
                    so = offset;
                }
                boundaryUpdater(range, sc, so, node, offset);
            }
        }

        function setRangeStartAndEnd(range, node, offset) {
            if (node !== range.startContainer || offset !== range.startOffset || node !== range.endContainer || offset !== range.endOffset) {
                boundaryUpdater(range, node, offset, node, offset);
            }
        }

        constructor.prototype = new RangePrototype();

        api.util.extend(constructor.prototype, {
            setStart: function(node, offset) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeStart(this, node, offset);
            },

            setEnd: function(node, offset) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeEnd(this, node, offset);
            },

            setStartBefore: createBeforeAfterNodeSetter(true, true),
            setStartAfter: createBeforeAfterNodeSetter(false, true),
            setEndBefore: createBeforeAfterNodeSetter(true, false),
            setEndAfter: createBeforeAfterNodeSetter(false, false),

            collapse: function(isStart) {
                assertRangeValid(this);
                if (isStart) {
                    boundaryUpdater(this, this.startContainer, this.startOffset, this.startContainer, this.startOffset);
                } else {
                    boundaryUpdater(this, this.endContainer, this.endOffset, this.endContainer, this.endOffset);
                }
            },

            selectNodeContents: function(node) {
                // This doesn't seem well specified: the spec talks only about selecting the node's contents, which
                // could be taken to mean only its children. However, browsers implement this the same as selectNode for
                // text nodes, so I shall do likewise
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);

                boundaryUpdater(this, node, 0, node, dom.getNodeLength(node));
            },

            selectNode: function(node) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, false);
                assertValidNodeType(node, beforeAfterNodeTypes);

                var start = getBoundaryBeforeNode(node), end = getBoundaryAfterNode(node);
                boundaryUpdater(this, start.node, start.offset, end.node, end.offset);
            },

            extractContents: createRangeContentRemover(extractSubtree, boundaryUpdater),

            deleteContents: createRangeContentRemover(deleteSubtree, boundaryUpdater),

            canSurroundContents: function() {
                assertRangeValid(this);
                assertNodeNotReadOnly(this.startContainer);
                assertNodeNotReadOnly(this.endContainer);

                // Check if the contents can be surrounded. Specifically, this means whether the range partially selects
                // no non-text nodes.
                var iterator = new RangeIterator(this, true);
                var boundariesInvalid = (iterator._first && (isNonTextPartiallySelected(iterator._first, this)) ||
                        (iterator._last && isNonTextPartiallySelected(iterator._last, this)));
                iterator.detach();
                return !boundariesInvalid;
            },

            detach: function() {
                detacher(this);
            },

            splitBoundaries: function() {
                assertRangeValid(this);


                var sc = this.startContainer, so = this.startOffset, ec = this.endContainer, eo = this.endOffset;
                var startEndSame = (sc === ec);

                if (dom.isCharacterDataNode(ec) && eo > 0 && eo < ec.length) {
                    dom.splitDataNode(ec, eo);

                }

                if (dom.isCharacterDataNode(sc) && so > 0 && so < sc.length) {

                    sc = dom.splitDataNode(sc, so);
                    if (startEndSame) {
                        eo -= so;
                        ec = sc;
                    } else if (ec == sc.parentNode && eo >= dom.getNodeIndex(sc)) {
                        eo++;
                    }
                    so = 0;

                }
                boundaryUpdater(this, sc, so, ec, eo);
            },

            normalizeBoundaries: function() {
                assertRangeValid(this);

                var sc = this.startContainer, so = this.startOffset, ec = this.endContainer, eo = this.endOffset;

                var mergeForward = function(node) {
                    var sibling = node.nextSibling;
                    if (sibling && sibling.nodeType == node.nodeType) {
                        ec = node;
                        eo = node.length;
                        node.appendData(sibling.data);
                        sibling.parentNode.removeChild(sibling);
                    }
                };

                var mergeBackward = function(node) {
                    var sibling = node.previousSibling;
                    if (sibling && sibling.nodeType == node.nodeType) {
                        sc = node;
                        var nodeLength = node.length;
                        so = sibling.length;
                        node.insertData(0, sibling.data);
                        sibling.parentNode.removeChild(sibling);
                        if (sc == ec) {
                            eo += so;
                            ec = sc;
                        } else if (ec == node.parentNode) {
                            var nodeIndex = dom.getNodeIndex(node);
                            if (eo == nodeIndex) {
                                ec = node;
                                eo = nodeLength;
                            } else if (eo > nodeIndex) {
                                eo--;
                            }
                        }
                    }
                };

                var normalizeStart = true;

                if (dom.isCharacterDataNode(ec)) {
                    if (ec.length == eo) {
                        mergeForward(ec);
                    }
                } else {
                    if (eo > 0) {
                        var endNode = ec.childNodes[eo - 1];
                        if (endNode && dom.isCharacterDataNode(endNode)) {
                            mergeForward(endNode);
                        }
                    }
                    normalizeStart = !this.collapsed;
                }

                if (normalizeStart) {
                    if (dom.isCharacterDataNode(sc)) {
                        if (so == 0) {
                            mergeBackward(sc);
                        }
                    } else {
                        if (so < sc.childNodes.length) {
                            var startNode = sc.childNodes[so];
                            if (startNode && dom.isCharacterDataNode(startNode)) {
                                mergeBackward(startNode);
                            }
                        }
                    }
                } else {
                    sc = ec;
                    so = eo;
                }

                boundaryUpdater(this, sc, so, ec, eo);
            },

            collapseToPoint: function(node, offset) {
                assertNotDetached(this);

                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeStartAndEnd(this, node, offset);
            }
        });

        copyComparisonConstants(constructor);
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Updates commonAncestorContainer and collapsed after boundary change
    function updateCollapsedAndCommonAncestor(range) {
        range.collapsed = (range.startContainer === range.endContainer && range.startOffset === range.endOffset);
        range.commonAncestorContainer = range.collapsed ?
            range.startContainer : dom.getCommonAncestor(range.startContainer, range.endContainer);
    }

    function updateBoundaries(range, startContainer, startOffset, endContainer, endOffset) {
        var startMoved = (range.startContainer !== startContainer || range.startOffset !== startOffset);
        var endMoved = (range.endContainer !== endContainer || range.endOffset !== endOffset);

        range.startContainer = startContainer;
        range.startOffset = startOffset;
        range.endContainer = endContainer;
        range.endOffset = endOffset;

        updateCollapsedAndCommonAncestor(range);
        dispatchEvent(range, "boundarychange", {startMoved: startMoved, endMoved: endMoved});
    }

    function detach(range) {
        assertNotDetached(range);
        range.startContainer = range.startOffset = range.endContainer = range.endOffset = null;
        range.collapsed = range.commonAncestorContainer = null;
        dispatchEvent(range, "detach", null);
        range._listeners = null;
    }

    /**
     * @constructor
     */
    function Range(doc) {
        this.startContainer = doc;
        this.startOffset = 0;
        this.endContainer = doc;
        this.endOffset = 0;
        this._listeners = {
            boundarychange: [],
            detach: []
        };
        updateCollapsedAndCommonAncestor(this);
    }

    createPrototypeRange(Range, updateBoundaries, detach);

    api.rangePrototype = RangePrototype.prototype;

    Range.rangeProperties = rangeProperties;
    Range.RangeIterator = RangeIterator;
    Range.copyComparisonConstants = copyComparisonConstants;
    Range.createPrototypeRange = createPrototypeRange;
    Range.inspect = inspect;
    Range.getRangeDocument = getRangeDocument;
    Range.rangesEqual = function(r1, r2) {
        return r1.startContainer === r2.startContainer &&
               r1.startOffset === r2.startOffset &&
               r1.endContainer === r2.endContainer &&
               r1.endOffset === r2.endOffset;
    };

    api.DomRange = Range;
    api.RangeException = RangeException;
});rangy.createModule("WrappedRange", function(api, module) {
    api.requireModules( ["DomUtil", "DomRange"] );

    /**
     * @constructor
     */
    var WrappedRange;
    var dom = api.dom;
    var DomPosition = dom.DomPosition;
    var DomRange = api.DomRange;



    /*----------------------------------------------------------------------------------------------------------------*/

    /*
    This is a workaround for a bug where IE returns the wrong container element from the TextRange's parentElement()
    method. For example, in the following (where pipes denote the selection boundaries):

    <ul id="ul"><li id="a">| a </li><li id="b"> b |</li></ul>

    var range = document.selection.createRange();
    alert(range.parentElement().id); // Should alert "ul" but alerts "b"

    This method returns the common ancestor node of the following:
    - the parentElement() of the textRange
    - the parentElement() of the textRange after calling collapse(true)
    - the parentElement() of the textRange after calling collapse(false)
     */
    function getTextRangeContainerElement(textRange) {
        var parentEl = textRange.parentElement();

        var range = textRange.duplicate();
        range.collapse(true);
        var startEl = range.parentElement();
        range = textRange.duplicate();
        range.collapse(false);
        var endEl = range.parentElement();
        var startEndContainer = (startEl == endEl) ? startEl : dom.getCommonAncestor(startEl, endEl);

        return startEndContainer == parentEl ? startEndContainer : dom.getCommonAncestor(parentEl, startEndContainer);
    }

    function textRangeIsCollapsed(textRange) {
        return textRange.compareEndPoints("StartToEnd", textRange) == 0;
    }

    // Gets the boundary of a TextRange expressed as a node and an offset within that node. This function started out as
    // an improved version of code found in Tim Cameron Ryan's IERange (http://code.google.com/p/ierange/) but has
    // grown, fixing problems with line breaks in preformatted text, adding workaround for IE TextRange bugs, handling
    // for inputs and images, plus optimizations.
    function getTextRangeBoundaryPosition(textRange, wholeRangeContainerElement, isStart, isCollapsed) {
        var workingRange = textRange.duplicate();

        workingRange.collapse(isStart);
        var containerElement = workingRange.parentElement();

        // Sometimes collapsing a TextRange that's at the start of a text node can move it into the previous node, so
        // check for that
        // TODO: Find out when. Workaround for wholeRangeContainerElement may break this
        if (!dom.isAncestorOf(wholeRangeContainerElement, containerElement, true)) {
            containerElement = wholeRangeContainerElement;

        }



        // Deal with nodes that cannot "contain rich HTML markup". In practice, this means form inputs, images and
        // similar. See http://msdn.microsoft.com/en-us/library/aa703950%28VS.85%29.aspx
        if (!containerElement.canHaveHTML) {
            return new DomPosition(containerElement.parentNode, dom.getNodeIndex(containerElement));
        }

        var workingNode = dom.getDocument(containerElement).createElement("span");
        var comparison, workingComparisonType = isStart ? "StartToStart" : "StartToEnd";
        var previousNode, nextNode, boundaryPosition, boundaryNode;

        // Move the working range through the container's children, starting at the end and working backwards, until the
        // working range reaches or goes past the boundary we're interested in
        do {
            containerElement.insertBefore(workingNode, workingNode.previousSibling);
            workingRange.moveToElementText(workingNode);
        } while ( (comparison = workingRange.compareEndPoints(workingComparisonType, textRange)) > 0 &&
                workingNode.previousSibling);

        // We've now reached or gone past the boundary of the text range we're interested in
        // so have identified the node we want
        boundaryNode = workingNode.nextSibling;

        if (comparison == -1 && boundaryNode && dom.isCharacterDataNode(boundaryNode)) {
            // This is a character data node (text, comment, cdata). The working range is collapsed at the start of the
            // node containing the text range's boundary, so we move the end of the working range to the boundary point
            // and measure the length of its text to get the boundary's offset within the node.
            workingRange.setEndPoint(isStart ? "EndToStart" : "EndToEnd", textRange);


            var offset;

            if (/[\r\n]/.test(boundaryNode.data)) {
                /*
                For the particular case of a boundary within a text node containing line breaks (within a <pre> element,
                for example), we need a slightly complicated approach to get the boundary's offset in IE. The facts:

                - Each line break is represented as \r in the text node's data/nodeValue properties
                - Each line break is represented as \r\n in the TextRange's 'text' property
                - The 'text' property of the TextRange does not contain trailing line breaks

                To get round the problem presented by the final fact above, we can use the fact that TextRange's
                moveStart() and moveEnd() methods return the actual number of characters moved, which is not necessarily
                the same as the number of characters it was instructed to move. The simplest approach is to use this to
                store the characters moved when moving both the start and end of the range to the start of the document
                body and subtracting the start offset from the end offset (the "move-negative-gazillion" method).
                However, this is extremely slow when the document is large and the range is near the end of it. Clearly
                doing the mirror image (i.e. moving the range boundaries to the end of the document) has the same
                problem.

                Another approach that works is to use moveStart() to move the start boundary of the range up to the end
                boundary one character at a time and incrementing a counter with the value returned by the moveStart()
                call. However, the check for whether the start boundary has reached the end boundary is expensive, so
                this method is slow (although unlike "move-negative-gazillion" is largely unaffected by the location of
                the range within the document).

                The method below is a hybrid of the two methods above. It uses the fact that a string containing the
                TextRange's 'text' property with each \r\n converted to a single \r character cannot be longer than the
                text of the TextRange, so the start of the range is moved that length initially and then a character at
                a time to make up for any trailing line breaks not contained in the 'text' property. This has good
                performance in most situations compared to the previous two methods.
                */
                var tempRange = workingRange.duplicate();
                var rangeLength = tempRange.text.replace(/\r\n/g, "\r").length;

                offset = tempRange.moveStart("character", rangeLength);
                while ( (comparison = tempRange.compareEndPoints("StartToEnd", tempRange)) == -1) {
                    offset++;
                    tempRange.moveStart("character", 1);
                }
            } else {
                offset = workingRange.text.length;
            }
            boundaryPosition = new DomPosition(boundaryNode, offset);
        } else {


            // If the boundary immediately follows a character data node and this is the end boundary, we should favour
            // a position within that, and likewise for a start boundary preceding a character data node
            previousNode = (isCollapsed || !isStart) && workingNode.previousSibling;
            nextNode = (isCollapsed || isStart) && workingNode.nextSibling;



            if (nextNode && dom.isCharacterDataNode(nextNode)) {
                boundaryPosition = new DomPosition(nextNode, 0);
            } else if (previousNode && dom.isCharacterDataNode(previousNode)) {
                boundaryPosition = new DomPosition(previousNode, previousNode.length);
            } else {
                boundaryPosition = new DomPosition(containerElement, dom.getNodeIndex(workingNode));
            }
        }

        // Clean up
        workingNode.parentNode.removeChild(workingNode);

        return boundaryPosition;
    }

    // Returns a TextRange representing the boundary of a TextRange expressed as a node and an offset within that node.
    // This function started out as an optimized version of code found in Tim Cameron Ryan's IERange
    // (http://code.google.com/p/ierange/)
    function createBoundaryTextRange(boundaryPosition, isStart) {
        var boundaryNode, boundaryParent, boundaryOffset = boundaryPosition.offset;
        var doc = dom.getDocument(boundaryPosition.node);
        var workingNode, childNodes, workingRange = doc.body.createTextRange();
        var nodeIsDataNode = dom.isCharacterDataNode(boundaryPosition.node);

        if (nodeIsDataNode) {
            boundaryNode = boundaryPosition.node;
            boundaryParent = boundaryNode.parentNode;
        } else {
            childNodes = boundaryPosition.node.childNodes;
            boundaryNode = (boundaryOffset < childNodes.length) ? childNodes[boundaryOffset] : null;
            boundaryParent = boundaryPosition.node;
        }

        // Position the range immediately before the node containing the boundary
        workingNode = doc.createElement("span");

        // Making the working element non-empty element persuades IE to consider the TextRange boundary to be within the
        // element rather than immediately before or after it, which is what we want
        workingNode.innerHTML = "&#feff;";

        // insertBefore is supposed to work like appendChild if the second parameter is null. However, a bug report
        // for IERange suggests that it can crash the browser: http://code.google.com/p/ierange/issues/detail?id=12
        if (boundaryNode) {
            boundaryParent.insertBefore(workingNode, boundaryNode);
        } else {
            boundaryParent.appendChild(workingNode);
        }

        workingRange.moveToElementText(workingNode);
        workingRange.collapse(!isStart);

        // Clean up
        boundaryParent.removeChild(workingNode);

        // Move the working range to the text offset, if required
        if (nodeIsDataNode) {
            workingRange[isStart ? "moveStart" : "moveEnd"]("character", boundaryOffset);
        }

        return workingRange;
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    if (api.features.implementsDomRange && (!api.features.implementsTextRange || !api.config.preferTextRange)) {
        // This is a wrapper around the browser's native DOM Range. It has two aims:
        // - Provide workarounds for specific browser bugs
        // - provide convenient extensions, which are inherited from Rangy's DomRange

        (function() {
            var rangeProto;
            var rangeProperties = DomRange.rangeProperties;
            var canSetRangeStartAfterEnd;

            function updateRangeProperties(range) {
                var i = rangeProperties.length, prop;
                while (i--) {
                    prop = rangeProperties[i];
                    range[prop] = range.nativeRange[prop];
                }
            }

            function updateNativeRange(range, startContainer, startOffset, endContainer,endOffset) {
                var startMoved = (range.startContainer !== startContainer || range.startOffset != startOffset);
                var endMoved = (range.endContainer !== endContainer || range.endOffset != endOffset);

                // Always set both boundaries for the benefit of IE9 (see issue 35)
                if (startMoved || endMoved) {
                    range.setEnd(endContainer, endOffset);
                    range.setStart(startContainer, startOffset);
                }
            }

            function detach(range) {
                range.nativeRange.detach();
                range.detached = true;
                var i = rangeProperties.length, prop;
                while (i--) {
                    prop = rangeProperties[i];
                    range[prop] = null;
                }
            }

            var createBeforeAfterNodeSetter;

            WrappedRange = function(range) {
                if (!range) {
                    throw new Error("Range must be specified");
                }
                this.nativeRange = range;
                updateRangeProperties(this);
            };

            DomRange.createPrototypeRange(WrappedRange, updateNativeRange, detach);

            rangeProto = WrappedRange.prototype;

            rangeProto.selectNode = function(node) {
                this.nativeRange.selectNode(node);
                updateRangeProperties(this);
            };

            rangeProto.deleteContents = function() {
                this.nativeRange.deleteContents();
                updateRangeProperties(this);
            };

            rangeProto.extractContents = function() {
                var frag = this.nativeRange.extractContents();
                updateRangeProperties(this);
                return frag;
            };

            rangeProto.cloneContents = function() {
                return this.nativeRange.cloneContents();
            };

            // TODO: Until I can find a way to programmatically trigger the Firefox bug (apparently long-standing, still
            // present in 3.6.8) that throws "Index or size is negative or greater than the allowed amount" for
            // insertNode in some circumstances, all browsers will have to use the Rangy's own implementation of
            // insertNode, which works but is almost certainly slower than the native implementation.
/*
            rangeProto.insertNode = function(node) {
                this.nativeRange.insertNode(node);
                updateRangeProperties(this);
            };
*/

            rangeProto.surroundContents = function(node) {
                this.nativeRange.surroundContents(node);
                updateRangeProperties(this);
            };

            rangeProto.collapse = function(isStart) {
                this.nativeRange.collapse(isStart);
                updateRangeProperties(this);
            };

            rangeProto.cloneRange = function() {
                return new WrappedRange(this.nativeRange.cloneRange());
            };

            rangeProto.refresh = function() {
                updateRangeProperties(this);
            };

            rangeProto.toString = function() {
                return this.nativeRange.toString();
            };

            // Create test range and node for feature detection

            var testTextNode = document.createTextNode("test");
            dom.getBody(document).appendChild(testTextNode);
            var range = document.createRange();

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for Firefox 2 bug that prevents moving the start of a Range to a point after its current end and
            // correct for it

            range.setStart(testTextNode, 0);
            range.setEnd(testTextNode, 0);

            try {
                range.setStart(testTextNode, 1);
                canSetRangeStartAfterEnd = true;

                rangeProto.setStart = function(node, offset) {
                    this.nativeRange.setStart(node, offset);
                    updateRangeProperties(this);
                };

                rangeProto.setEnd = function(node, offset) {
                    this.nativeRange.setEnd(node, offset);
                    updateRangeProperties(this);
                };

                createBeforeAfterNodeSetter = function(name) {
                    return function(node) {
                        this.nativeRange[name](node);
                        updateRangeProperties(this);
                    };
                };

            } catch(ex) {


                canSetRangeStartAfterEnd = false;

                rangeProto.setStart = function(node, offset) {
                    try {
                        this.nativeRange.setStart(node, offset);
                    } catch (ex) {
                        this.nativeRange.setEnd(node, offset);
                        this.nativeRange.setStart(node, offset);
                    }
                    updateRangeProperties(this);
                };

                rangeProto.setEnd = function(node, offset) {
                    try {
                        this.nativeRange.setEnd(node, offset);
                    } catch (ex) {
                        this.nativeRange.setStart(node, offset);
                        this.nativeRange.setEnd(node, offset);
                    }
                    updateRangeProperties(this);
                };

                createBeforeAfterNodeSetter = function(name, oppositeName) {
                    return function(node) {
                        try {
                            this.nativeRange[name](node);
                        } catch (ex) {
                            this.nativeRange[oppositeName](node);
                            this.nativeRange[name](node);
                        }
                        updateRangeProperties(this);
                    };
                };
            }

            rangeProto.setStartBefore = createBeforeAfterNodeSetter("setStartBefore", "setEndBefore");
            rangeProto.setStartAfter = createBeforeAfterNodeSetter("setStartAfter", "setEndAfter");
            rangeProto.setEndBefore = createBeforeAfterNodeSetter("setEndBefore", "setStartBefore");
            rangeProto.setEndAfter = createBeforeAfterNodeSetter("setEndAfter", "setStartAfter");

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for and correct Firefox 2 behaviour with selectNodeContents on text nodes: it collapses the range to
            // the 0th character of the text node
            range.selectNodeContents(testTextNode);
            if (range.startContainer == testTextNode && range.endContainer == testTextNode &&
                    range.startOffset == 0 && range.endOffset == testTextNode.length) {
                rangeProto.selectNodeContents = function(node) {
                    this.nativeRange.selectNodeContents(node);
                    updateRangeProperties(this);
                };
            } else {
                rangeProto.selectNodeContents = function(node) {
                    this.setStart(node, 0);
                    this.setEnd(node, DomRange.getEndOffset(node));
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for WebKit bug that has the beahviour of compareBoundaryPoints round the wrong way for constants
            // START_TO_END and END_TO_START: https://bugs.webkit.org/show_bug.cgi?id=20738

            range.selectNodeContents(testTextNode);
            range.setEnd(testTextNode, 3);

            var range2 = document.createRange();
            range2.selectNodeContents(testTextNode);
            range2.setEnd(testTextNode, 4);
            range2.setStart(testTextNode, 2);

            if (range.compareBoundaryPoints(range.START_TO_END, range2) == -1 &
                    range.compareBoundaryPoints(range.END_TO_START, range2) == 1) {
                // This is the wrong way round, so correct for it


                rangeProto.compareBoundaryPoints = function(type, range) {
                    range = range.nativeRange || range;
                    if (type == range.START_TO_END) {
                        type = range.END_TO_START;
                    } else if (type == range.END_TO_START) {
                        type = range.START_TO_END;
                    }
                    return this.nativeRange.compareBoundaryPoints(type, range);
                };
            } else {
                rangeProto.compareBoundaryPoints = function(type, range) {
                    return this.nativeRange.compareBoundaryPoints(type, range.nativeRange || range);
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for existence of createContextualFragment and delegate to it if it exists
            if (api.util.isHostMethod(range, "createContextualFragment")) {
                rangeProto.createContextualFragment = function(fragmentStr) {
                    return this.nativeRange.createContextualFragment(fragmentStr);
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Clean up
            dom.getBody(document).removeChild(testTextNode);
            range.detach();
            range2.detach();
        })();

        api.createNativeRange = function(doc) {
            doc = doc || document;
            return doc.createRange();
        };
    } else if (api.features.implementsTextRange) {
        // This is a wrapper around a TextRange, providing full DOM Range functionality using rangy's DomRange as a
        // prototype

        WrappedRange = function(textRange) {
            this.textRange = textRange;
            this.refresh();
        };

        WrappedRange.prototype = new DomRange(document);

        WrappedRange.prototype.refresh = function() {
            var start, end;

            // TextRange's parentElement() method cannot be trusted. getTextRangeContainerElement() works around that.
            var rangeContainerElement = getTextRangeContainerElement(this.textRange);

            if (textRangeIsCollapsed(this.textRange)) {
                end = start = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, true, true);
            } else {

                start = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, true, false);
                end = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, false, false);
            }

            this.setStart(start.node, start.offset);
            this.setEnd(end.node, end.offset);
        };

        DomRange.copyComparisonConstants(WrappedRange);

        // Add WrappedRange as the Range property of the global object to allow expression like Range.END_TO_END to work
        var globalObj = (function() { return this; })();
        if (typeof globalObj.Range == "undefined") {
            globalObj.Range = WrappedRange;
        }

        api.createNativeRange = function(doc) {
            doc = doc || document;
            return doc.body.createTextRange();
        };
    }

    if (api.features.implementsTextRange) {
        WrappedRange.rangeToTextRange = function(range) {
            if (range.collapsed) {
                var tr = createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);



                return tr;

                //return createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);
            } else {
                var startRange = createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);
                var endRange = createBoundaryTextRange(new DomPosition(range.endContainer, range.endOffset), false);
                var textRange = dom.getDocument(range.startContainer).body.createTextRange();
                textRange.setEndPoint("StartToStart", startRange);
                textRange.setEndPoint("EndToEnd", endRange);
                return textRange;
            }
        };
    }

    WrappedRange.prototype.getName = function() {
        return "WrappedRange";
    };

    api.WrappedRange = WrappedRange;

    api.createRange = function(doc) {
        doc = doc || document;
        return new WrappedRange(api.createNativeRange(doc));
    };

    api.createRangyRange = function(doc) {
        doc = doc || document;
        return new DomRange(doc);
    };

    api.createIframeRange = function(iframeEl) {
        return api.createRange(dom.getIframeDocument(iframeEl));
    };

    api.createIframeRangyRange = function(iframeEl) {
        return api.createRangyRange(dom.getIframeDocument(iframeEl));
    };

    api.addCreateMissingNativeApiListener(function(win) {
        var doc = win.document;
        if (typeof doc.createRange == "undefined") {
            doc.createRange = function() {
                return api.createRange(this);
            };
        }
        doc = win = null;
    });
});rangy.createModule("WrappedSelection", function(api, module) {
    // This will create a selection object wrapper that follows the Selection object found in the WHATWG draft DOM Range
    // spec (http://html5.org/specs/dom-range.html)

    api.requireModules( ["DomUtil", "DomRange", "WrappedRange"] );

    api.config.checkSelectionRanges = true;

    var BOOLEAN = "boolean",
        windowPropertyName = "_rangySelection",
        dom = api.dom,
        util = api.util,
        DomRange = api.DomRange,
        WrappedRange = api.WrappedRange,
        DOMException = api.DOMException,
        DomPosition = dom.DomPosition,
        getSelection,
        selectionIsCollapsed,
        CONTROL = "Control";



    function getWinSelection(winParam) {
        return (winParam || window).getSelection();
    }

    function getDocSelection(winParam) {
        return (winParam || window).document.selection;
    }

    // Test for the Range/TextRange and Selection features required
    // Test for ability to retrieve selection
    var implementsWinGetSelection = api.util.isHostMethod(window, "getSelection"),
        implementsDocSelection = api.util.isHostObject(document, "selection");

    var useDocumentSelection = implementsDocSelection && (!implementsWinGetSelection || api.config.preferTextRange);

    if (useDocumentSelection) {
        getSelection = getDocSelection;
        api.isSelectionValid = function(winParam) {
            var doc = (winParam || window).document, nativeSel = doc.selection;

            // Check whether the selection TextRange is actually contained within the correct document
            return (nativeSel.type != "None" || dom.getDocument(nativeSel.createRange().parentElement()) == doc);
        };
    } else if (implementsWinGetSelection) {
        getSelection = getWinSelection;
        api.isSelectionValid = function() {
            return true;
        };
    } else {
        module.fail("Neither document.selection or window.getSelection() detected.");
    }

    api.getNativeSelection = getSelection;

    var testSelection = getSelection();
    var testRange = api.createNativeRange(document);
    var body = dom.getBody(document);

    // Obtaining a range from a selection
    var selectionHasAnchorAndFocus = util.areHostObjects(testSelection, ["anchorNode", "focusNode"] &&
                                     util.areHostProperties(testSelection, ["anchorOffset", "focusOffset"]));
    api.features.selectionHasAnchorAndFocus = selectionHasAnchorAndFocus;

    // Test for existence of native selection extend() method
    var selectionHasExtend = util.isHostMethod(testSelection, "extend");
    api.features.selectionHasExtend = selectionHasExtend;

    // Test if rangeCount exists
    var selectionHasRangeCount = (typeof testSelection.rangeCount == "number");
    api.features.selectionHasRangeCount = selectionHasRangeCount;

    var selectionSupportsMultipleRanges = false;
    var collapsedNonEditableSelectionsSupported = true;

    if (util.areHostMethods(testSelection, ["addRange", "getRangeAt", "removeAllRanges"]) &&
            typeof testSelection.rangeCount == "number" && api.features.implementsDomRange) {

        (function() {
            var iframe = document.createElement("iframe");
            iframe.frameBorder = 0;
            iframe.style.position = "absolute";
            iframe.style.left = "-10000px";
            body.appendChild(iframe);

            var iframeDoc = dom.getIframeDocument(iframe);
            iframeDoc.open();
            iframeDoc.write("<html><head></head><body>12</body></html>");
            iframeDoc.close();

            var sel = dom.getIframeWindow(iframe).getSelection();
            var docEl = iframeDoc.documentElement;
            var iframeBody = docEl.lastChild, textNode = iframeBody.firstChild;

            // Test whether the native selection will allow a collapsed selection within a non-editable element
            var r1 = iframeDoc.createRange();
            r1.setStart(textNode, 1);
            r1.collapse(true);
            sel.addRange(r1);
            collapsedNonEditableSelectionsSupported = (sel.rangeCount == 1);
            sel.removeAllRanges();

            // Test whether the native selection is capable of supporting multiple ranges
            var r2 = r1.cloneRange();
            r1.setStart(textNode, 0);
            r2.setEnd(textNode, 2);
            sel.addRange(r1);
            sel.addRange(r2);

            selectionSupportsMultipleRanges = (sel.rangeCount == 2);

            // Clean up
            r1.detach();
            r2.detach();

            body.removeChild(iframe);
        })();
    }

    api.features.selectionSupportsMultipleRanges = selectionSupportsMultipleRanges;
    api.features.collapsedNonEditableSelectionsSupported = collapsedNonEditableSelectionsSupported;

    // ControlRanges
    var implementsControlRange = false, testControlRange;

    if (body && util.isHostMethod(body, "createControlRange")) {
        testControlRange = body.createControlRange();
        if (util.areHostProperties(testControlRange, ["item", "add"])) {
            implementsControlRange = true;
        }
    }
    api.features.implementsControlRange = implementsControlRange;

    // Selection collapsedness
    if (selectionHasAnchorAndFocus) {
        selectionIsCollapsed = function(sel) {
            return sel.anchorNode === sel.focusNode && sel.anchorOffset === sel.focusOffset;
        };
    } else {
        selectionIsCollapsed = function(sel) {
            return sel.rangeCount ? sel.getRangeAt(sel.rangeCount - 1).collapsed : false;
        };
    }

    function updateAnchorAndFocusFromRange(sel, range, backwards) {
        var anchorPrefix = backwards ? "end" : "start", focusPrefix = backwards ? "start" : "end";
        sel.anchorNode = range[anchorPrefix + "Container"];
        sel.anchorOffset = range[anchorPrefix + "Offset"];
        sel.focusNode = range[focusPrefix + "Container"];
        sel.focusOffset = range[focusPrefix + "Offset"];
    }

    function updateAnchorAndFocusFromNativeSelection(sel) {
        var nativeSel = sel.nativeSelection;
        sel.anchorNode = nativeSel.anchorNode;
        sel.anchorOffset = nativeSel.anchorOffset;
        sel.focusNode = nativeSel.focusNode;
        sel.focusOffset = nativeSel.focusOffset;
    }

    function updateEmptySelection(sel) {
        sel.anchorNode = sel.focusNode = null;
        sel.anchorOffset = sel.focusOffset = 0;
        sel.rangeCount = 0;
        sel.isCollapsed = true;
        sel._ranges.length = 0;
    }

    function getNativeRange(range) {
        var nativeRange;
        if (range instanceof DomRange) {
            nativeRange = range._selectionNativeRange;
            if (!nativeRange) {
                nativeRange = api.createNativeRange(dom.getDocument(range.startContainer));
                nativeRange.setEnd(range.endContainer, range.endOffset);
                nativeRange.setStart(range.startContainer, range.startOffset);
                range._selectionNativeRange = nativeRange;
                range.attachListener("detach", function() {

                    this._selectionNativeRange = null;
                });
            }
        } else if (range instanceof WrappedRange) {
            nativeRange = range.nativeRange;
        } else if (api.features.implementsDomRange && (range instanceof dom.getWindow(range.startContainer).Range)) {
            nativeRange = range;
        }
        return nativeRange;
    }

    function rangeContainsSingleElement(rangeNodes) {
        if (!rangeNodes.length || rangeNodes[0].nodeType != 1) {
            return false;
        }
        for (var i = 1, len = rangeNodes.length; i < len; ++i) {
            if (!dom.isAncestorOf(rangeNodes[0], rangeNodes[i])) {
                return false;
            }
        }
        return true;
    }

    function getSingleElementFromRange(range) {
        var nodes = range.getNodes();
        if (!rangeContainsSingleElement(nodes)) {
            throw new Error("getSingleElementFromRange: range " + range.inspect() + " did not consist of a single element");
        }
        return nodes[0];
    }

    function isTextRange(range) {
        return !!range && typeof range.text != "undefined";
    }

    function updateFromTextRange(sel, range) {
        // Create a Range from the selected TextRange
        var wrappedRange = new WrappedRange(range);
        sel._ranges = [wrappedRange];

        updateAnchorAndFocusFromRange(sel, wrappedRange, false);
        sel.rangeCount = 1;
        sel.isCollapsed = wrappedRange.collapsed;
    }

    function updateControlSelection(sel) {
        // Update the wrapped selection based on what's now in the native selection
        sel._ranges.length = 0;
        if (sel.docSelection.type == "None") {
            updateEmptySelection(sel);
        } else {
            var controlRange = sel.docSelection.createRange();
            if (isTextRange(controlRange)) {
                // This case (where the selection type is "Control" and calling createRange() on the selection returns
                // a TextRange) can happen in IE 9. It happens, for example, when all elements in the selected
                // ControlRange have been removed from the ControlRange and removed from the document.
                updateFromTextRange(sel, controlRange);
            } else {
                sel.rangeCount = controlRange.length;
                var range, doc = dom.getDocument(controlRange.item(0));
                for (var i = 0; i < sel.rangeCount; ++i) {
                    range = api.createRange(doc);
                    range.selectNode(controlRange.item(i));
                    sel._ranges.push(range);
                }
                sel.isCollapsed = sel.rangeCount == 1 && sel._ranges[0].collapsed;
                updateAnchorAndFocusFromRange(sel, sel._ranges[sel.rangeCount - 1], false);
            }
        }
    }

    function addRangeToControlSelection(sel, range) {
        var controlRange = sel.docSelection.createRange();
        var rangeElement = getSingleElementFromRange(range);

        // Create a new ControlRange containing all the elements in the selected ControlRange plus the element
        // contained by the supplied range
        var doc = dom.getDocument(controlRange.item(0));
        var newControlRange = dom.getBody(doc).createControlRange();
        for (var i = 0, len = controlRange.length; i < len; ++i) {
            newControlRange.add(controlRange.item(i));
        }
        try {
            newControlRange.add(rangeElement);
        } catch (ex) {
            throw new Error("addRange(): Element within the specified Range could not be added to control selection (does it have layout?)");
        }
        newControlRange.select();

        // Update the wrapped selection based on what's now in the native selection
        updateControlSelection(sel);
    }

    var getSelectionRangeAt;

    if (util.isHostMethod(testSelection,  "getRangeAt")) {
        getSelectionRangeAt = function(sel, index) {
            try {
                return sel.getRangeAt(index);
            } catch(ex) {
                return null;
            }
        };
    } else if (selectionHasAnchorAndFocus) {
        getSelectionRangeAt = function(sel) {
            var doc = dom.getDocument(sel.anchorNode);
            var range = api.createRange(doc);
            range.setStart(sel.anchorNode, sel.anchorOffset);
            range.setEnd(sel.focusNode, sel.focusOffset);

            // Handle the case when the selection was selected backwards (from the end to the start in the
            // document)
            if (range.collapsed !== this.isCollapsed) {
                range.setStart(sel.focusNode, sel.focusOffset);
                range.setEnd(sel.anchorNode, sel.anchorOffset);
            }

            return range;
        };
    }

    /**
     * @constructor
     */
    function WrappedSelection(selection, docSelection, win) {
        this.nativeSelection = selection;
        this.docSelection = docSelection;
        this._ranges = [];
        this.win = win;
        this.refresh();
    }

    api.getSelection = function(win) {
        win = win || window;
        var sel = win[windowPropertyName];
        var nativeSel = getSelection(win), docSel = implementsDocSelection ? getDocSelection(win) : null;
        if (sel) {
            sel.nativeSelection = nativeSel;
            sel.docSelection = docSel;
            sel.refresh(win);
        } else {
            sel = new WrappedSelection(nativeSel, docSel, win);
            win[windowPropertyName] = sel;
        }
        return sel;
    };

    api.getIframeSelection = function(iframeEl) {
        return api.getSelection(dom.getIframeWindow(iframeEl));
    };

    var selProto = WrappedSelection.prototype;

    function createControlSelection(sel, ranges) {
        // Ensure that the selection becomes of type "Control"
        var doc = dom.getDocument(ranges[0].startContainer);
        var controlRange = dom.getBody(doc).createControlRange();
        for (var i = 0, el; i < rangeCount; ++i) {
            el = getSingleElementFromRange(ranges[i]);
            try {
                controlRange.add(el);
            } catch (ex) {
                throw new Error("setRanges(): Element within the one of the specified Ranges could not be added to control selection (does it have layout?)");
            }
        }
        controlRange.select();

        // Update the wrapped selection based on what's now in the native selection
        updateControlSelection(sel);
    }

    // Selecting a range
    if (!useDocumentSelection && selectionHasAnchorAndFocus && util.areHostMethods(testSelection, ["removeAllRanges", "addRange"])) {
        selProto.removeAllRanges = function() {
            this.nativeSelection.removeAllRanges();
            updateEmptySelection(this);
        };

        var addRangeBackwards = function(sel, range) {
            var doc = DomRange.getRangeDocument(range);
            var endRange = api.createRange(doc);
            endRange.collapseToPoint(range.endContainer, range.endOffset);
            sel.nativeSelection.addRange(getNativeRange(endRange));
            sel.nativeSelection.extend(range.startContainer, range.startOffset);
            sel.refresh();
        };

        if (selectionHasRangeCount) {
            selProto.addRange = function(range, backwards) {
                if (implementsControlRange && implementsDocSelection && this.docSelection.type == CONTROL) {
                    addRangeToControlSelection(this, range);
                } else {
                    if (backwards && selectionHasExtend) {
                        addRangeBackwards(this, range);
                    } else {
                        var previousRangeCount;
                        if (selectionSupportsMultipleRanges) {
                            previousRangeCount = this.rangeCount;
                        } else {
                            this.removeAllRanges();
                            previousRangeCount = 0;
                        }
                        this.nativeSelection.addRange(getNativeRange(range));

                        // Check whether adding the range was successful
                        this.rangeCount = this.nativeSelection.rangeCount;

                        if (this.rangeCount == previousRangeCount + 1) {
                            // The range was added successfully

                            // Check whether the range that we added to the selection is reflected in the last range extracted from
                            // the selection
                            if (api.config.checkSelectionRanges) {
                                var nativeRange = getSelectionRangeAt(this.nativeSelection, this.rangeCount - 1);
                                if (nativeRange && !DomRange.rangesEqual(nativeRange, range)) {
                                    // Happens in WebKit with, for example, a selection placed at the start of a text node
                                    range = new WrappedRange(nativeRange);
                                }
                            }
                            this._ranges[this.rangeCount - 1] = range;
                            updateAnchorAndFocusFromRange(this, range, selectionIsBackwards(this.nativeSelection));
                            this.isCollapsed = selectionIsCollapsed(this);
                        } else {
                            // The range was not added successfully. The simplest thing is to refresh
                            this.refresh();
                        }
                    }
                }
            };
        } else {
            selProto.addRange = function(range, backwards) {
                if (backwards && selectionHasExtend) {
                    addRangeBackwards(this, range);
                } else {
                    this.nativeSelection.addRange(getNativeRange(range));
                    this.refresh();
                }
            };
        }

        selProto.setRanges = function(ranges) {
            if (implementsControlRange && ranges.length > 1) {
                createControlSelection(this, ranges);
            } else {
                this.removeAllRanges();
                for (var i = 0, len = ranges.length; i < len; ++i) {
                    this.addRange(ranges[i]);
                }
            }
        };
    } else if (util.isHostMethod(testSelection, "empty") && util.isHostMethod(testRange, "select") &&
               implementsControlRange && useDocumentSelection) {

        selProto.removeAllRanges = function() {
            // Added try/catch as fix for issue #21
            try {
                this.docSelection.empty();

                // Check for empty() not working (issue #24)
                if (this.docSelection.type != "None") {
                    // Work around failure to empty a control selection by instead selecting a TextRange and then
                    // calling empty()
                    var doc;
                    if (this.anchorNode) {
                        doc = dom.getDocument(this.anchorNode);
                    } else if (this.docSelection.type == CONTROL) {
                        var controlRange = this.docSelection.createRange();
                        if (controlRange.length) {
                            doc = dom.getDocument(controlRange.item(0)).body.createTextRange();
                        }
                    }
                    if (doc) {
                        var textRange = doc.body.createTextRange();
                        textRange.select();
                        this.docSelection.empty();
                    }
                }
            } catch(ex) {}
            updateEmptySelection(this);
        };

        selProto.addRange = function(range) {
            if (this.docSelection.type == CONTROL) {
                addRangeToControlSelection(this, range);
            } else {
                WrappedRange.rangeToTextRange(range).select();
                this._ranges[0] = range;
                this.rangeCount = 1;
                this.isCollapsed = this._ranges[0].collapsed;
                updateAnchorAndFocusFromRange(this, range, false);
            }
        };

        selProto.setRanges = function(ranges) {
            this.removeAllRanges();
            var rangeCount = ranges.length;
            if (rangeCount > 1) {
                createControlSelection(this, ranges);
            } else if (rangeCount) {
                this.addRange(ranges[0]);
            }
        };
    } else {
        module.fail("No means of selecting a Range or TextRange was found");
        return false;
    }

    selProto.getRangeAt = function(index) {
        if (index < 0 || index >= this.rangeCount) {
            throw new DOMException("INDEX_SIZE_ERR");
        } else {
            return this._ranges[index];
        }
    };

    var refreshSelection;

    if (useDocumentSelection) {
        refreshSelection = function(sel) {
            var range;
            if (api.isSelectionValid(sel.win)) {
                range = sel.docSelection.createRange();
            } else {
                range = dom.getBody(sel.win.document).createTextRange();
                range.collapse(true);
            }


            if (sel.docSelection.type == CONTROL) {
                updateControlSelection(sel);
            } else if (isTextRange(range)) {
                updateFromTextRange(sel, range);
            } else {
                updateEmptySelection(sel);
            }
        };
    } else if (util.isHostMethod(testSelection, "getRangeAt") && typeof testSelection.rangeCount == "number") {
        refreshSelection = function(sel) {
            if (implementsControlRange && implementsDocSelection && sel.docSelection.type == CONTROL) {
                updateControlSelection(sel);
            } else {
                sel._ranges.length = sel.rangeCount = sel.nativeSelection.rangeCount;
                if (sel.rangeCount) {
                    for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                        sel._ranges[i] = new api.WrappedRange(sel.nativeSelection.getRangeAt(i));
                    }
                    updateAnchorAndFocusFromRange(sel, sel._ranges[sel.rangeCount - 1], selectionIsBackwards(sel.nativeSelection));
                    sel.isCollapsed = selectionIsCollapsed(sel);
                } else {
                    updateEmptySelection(sel);
                }
            }
        };
    } else if (selectionHasAnchorAndFocus && typeof testSelection.isCollapsed == BOOLEAN && typeof testRange.collapsed == BOOLEAN && api.features.implementsDomRange) {
        refreshSelection = function(sel) {
            var range, nativeSel = sel.nativeSelection;
            if (nativeSel.anchorNode) {
                range = getSelectionRangeAt(nativeSel, 0);
                sel._ranges = [range];
                sel.rangeCount = 1;
                updateAnchorAndFocusFromNativeSelection(sel);
                sel.isCollapsed = selectionIsCollapsed(sel);
            } else {
                updateEmptySelection(sel);
            }
        };
    } else {
        module.fail("No means of obtaining a Range or TextRange from the user's selection was found");
        return false;
    }

    selProto.refresh = function(checkForChanges) {
        var oldRanges = checkForChanges ? this._ranges.slice(0) : null;
        refreshSelection(this);
        if (checkForChanges) {
            var i = oldRanges.length;
            if (i != this._ranges.length) {
                return false;
            }
            while (i--) {
                if (!DomRange.rangesEqual(oldRanges[i], this._ranges[i])) {
                    return false;
                }
            }
            return true;
        }
    };

    // Removal of a single range
    var removeRangeManually = function(sel, range) {
        var ranges = sel.getAllRanges(), removed = false;
        sel.removeAllRanges();
        for (var i = 0, len = ranges.length; i < len; ++i) {
            if (removed || range !== ranges[i]) {
                sel.addRange(ranges[i]);
            } else {
                // According to the draft WHATWG Range spec, the same range may be added to the selection multiple
                // times. removeRange should only remove the first instance, so the following ensures only the first
                // instance is removed
                removed = true;
            }
        }
        if (!sel.rangeCount) {
            updateEmptySelection(sel);
        }
    };

    if (implementsControlRange) {
        selProto.removeRange = function(range) {
            if (this.docSelection.type == CONTROL) {
                var controlRange = this.docSelection.createRange();
                var rangeElement = getSingleElementFromRange(range);

                // Create a new ControlRange containing all the elements in the selected ControlRange minus the
                // element contained by the supplied range
                var doc = dom.getDocument(controlRange.item(0));
                var newControlRange = dom.getBody(doc).createControlRange();
                var el, removed = false;
                for (var i = 0, len = controlRange.length; i < len; ++i) {
                    el = controlRange.item(i);
                    if (el !== rangeElement || removed) {
                        newControlRange.add(controlRange.item(i));
                    } else {
                        removed = true;
                    }
                }
                newControlRange.select();

                // Update the wrapped selection based on what's now in the native selection
                updateControlSelection(this);
            } else {
                removeRangeManually(this, range);
            }
        };
    } else {
        selProto.removeRange = function(range) {
            removeRangeManually(this, range);
        };
    }

    // Detecting if a selection is backwards
    var selectionIsBackwards;
    if (!useDocumentSelection && selectionHasAnchorAndFocus && api.features.implementsDomRange) {
        selectionIsBackwards = function(sel) {
            var backwards = false;
            if (sel.anchorNode) {
                backwards = (dom.comparePoints(sel.anchorNode, sel.anchorOffset, sel.focusNode, sel.focusOffset) == 1);
            }
            return backwards;
        };

        selProto.isBackwards = function() {
            return selectionIsBackwards(this);
        };
    } else {
        selectionIsBackwards = selProto.isBackwards = function() {
            return false;
        };
    }

    // Selection text
    // This is conformant to the new WHATWG DOM Range draft spec but differs from WebKit and Mozilla's implementation
    selProto.toString = function() {

        var rangeTexts = [];
        for (var i = 0, len = this.rangeCount; i < len; ++i) {
            rangeTexts[i] = "" + this._ranges[i];
        }
        return rangeTexts.join("");
    };

    function assertNodeInSameDocument(sel, node) {
        if (sel.anchorNode && (dom.getDocument(sel.anchorNode) !== dom.getDocument(node))) {
            throw new DOMException("WRONG_DOCUMENT_ERR");
        }
    }

    // No current browsers conform fully to the HTML 5 draft spec for this method, so Rangy's own method is always used
    selProto.collapse = function(node, offset) {
        assertNodeInSameDocument(this, node);
        var range = api.createRange(dom.getDocument(node));
        range.collapseToPoint(node, offset);
        this.removeAllRanges();
        this.addRange(range);
        this.isCollapsed = true;
    };

    selProto.collapseToStart = function() {
        if (this.rangeCount) {
            var range = this._ranges[0];
            this.collapse(range.startContainer, range.startOffset);
        } else {
            throw new DOMException("INVALID_STATE_ERR");
        }
    };

    selProto.collapseToEnd = function() {
        if (this.rangeCount) {
            var range = this._ranges[this.rangeCount - 1];
            this.collapse(range.endContainer, range.endOffset);
        } else {
            throw new DOMException("INVALID_STATE_ERR");
        }
    };

    // The HTML 5 spec is very specific on how selectAllChildren should be implemented so the native implementation is
    // never used by Rangy.
    selProto.selectAllChildren = function(node) {
        assertNodeInSameDocument(this, node);
        var range = api.createRange(dom.getDocument(node));
        range.selectNodeContents(node);
        this.removeAllRanges();
        this.addRange(range);
    };

    selProto.deleteFromDocument = function() {
        // Sepcial behaviour required for Control selections
        if (implementsControlRange && implementsDocSelection && this.docSelection.type == CONTROL) {
            var controlRange = this.docSelection.createRange();
            var element;
            while (controlRange.length) {
                element = controlRange.item(0);
                controlRange.remove(element);
                element.parentNode.removeChild(element);
            }
            this.refresh();
        } else if (this.rangeCount) {
            var ranges = this.getAllRanges();
            this.removeAllRanges();
            for (var i = 0, len = ranges.length; i < len; ++i) {
                ranges[i].deleteContents();
            }
            // The HTML5 spec says nothing about what the selection should contain after calling deleteContents on each
            // range. Firefox moves the selection to where the final selected range was, so we emulate that
            this.addRange(ranges[len - 1]);
        }
    };

    // The following are non-standard extensions
    selProto.getAllRanges = function() {
        return this._ranges.slice(0);
    };

    selProto.setSingleRange = function(range) {
        this.setRanges( [range] );
    };

    selProto.containsNode = function(node, allowPartial) {
        for (var i = 0, len = this._ranges.length; i < len; ++i) {
            if (this._ranges[i].containsNode(node, allowPartial)) {
                return true;
            }
        }
        return false;
    };

    selProto.toHtml = function() {
        var html = "";
        if (this.rangeCount) {
            var container = DomRange.getRangeDocument(this._ranges[0]).createElement("div");
            for (var i = 0, len = this._ranges.length; i < len; ++i) {
                container.appendChild(this._ranges[i].cloneContents());
            }
            html = container.innerHTML;
        }
        return html;
    };

    function inspect(sel) {
        var rangeInspects = [];
        var anchor = new DomPosition(sel.anchorNode, sel.anchorOffset);
        var focus = new DomPosition(sel.focusNode, sel.focusOffset);
        var name = (typeof sel.getName == "function") ? sel.getName() : "Selection";

        if (typeof sel.rangeCount != "undefined") {
            for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                rangeInspects[i] = DomRange.inspect(sel.getRangeAt(i));
            }
        }
        return "[" + name + "(Ranges: " + rangeInspects.join(", ") +
                ")(anchor: " + anchor.inspect() + ", focus: " + focus.inspect() + "]";

    }

    selProto.getName = function() {
        return "WrappedSelection";
    };

    selProto.inspect = function() {
        return inspect(this);
    };

    selProto.detach = function() {
        this.win[windowPropertyName] = null;
        this.win = this.anchorNode = this.focusNode = null;
    };

    WrappedSelection.inspect = inspect;

    api.Selection = WrappedSelection;

    api.selectionPrototype = selProto;

    api.addCreateMissingNativeApiListener(function(win) {
        if (typeof win.getSelection == "undefined") {
            win.getSelection = function() {
                return api.getSelection(this);
            };
        }
        win = null;
    });
});

// Add ECMA262-5 string trim if not supported natively
//
if (typeof String.prototype.trim !== 'function') {
  String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/g, '');
  }
}

// Add ECMA262-5 Array methods if not supported natively
//
if (!('indexOf' in Array.prototype)) {
  Array.prototype.indexOf= function(find, i /*opt*/) {
    if (i===undefined) i= 0;
    if (i<0) i+= this.length;
    if (i<0) i= 0;
    for (var n= this.length; i<n; i++)
      if (i in this && this[i]===find)
        return i;
    return -1;
  };
}
if (!('lastIndexOf' in Array.prototype)) {
  Array.prototype.lastIndexOf= function(find, i /*opt*/) {
    if (i===undefined) i= this.length-1;
    if (i<0) i+= this.length;
    if (i>this.length-1) i= this.length-1;
    for (i++; i-->0;) /* i++ because from-argument is sadly inclusive */
      if (i in this && this[i]===find)
        return i;
    return -1;
  };
}
if (!('map' in Array.prototype)) {
  Array.prototype.map= function(mapper, that /*opt*/) {
    var other= new Array(this.length);
    for (var i= 0, n= this.length; i<n; i++)
      if (i in this)
        other[i]= mapper.call(that, this[i], i, this);
    return other;
  };
}
if (!('filter' in Array.prototype)) {
  Array.prototype.filter= function(filter, that /*opt*/) {
    var other= [], v;
    for (var i=0, n= this.length; i<n; i++)
      if (i in this && filter.call(that, v= this[i], i, this))
        other.push(v);
    return other;
  };
}

(function () {

  var exports = this,
    defaults, InlineChangeEditor;

  defaults = {
    // ice node attribute names:
    changeIdAttribute: 'data-cid',
    userIdAttribute: 'data-userid',
    userNameAttribute: 'data-username',
    timeAttribute: 'data-time',

    // Prepended to `changeType.alias` for classname uniqueness, if needed
    attrValuePrefix: '',

    // Block element tagname, which wrap text and other inline nodes in `this.element`
    blockEl: 'p',

    // All permitted block element tagnames
    blockEls: ['p', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'],

    // Unique style prefix, prepended to a digit, incremented for each encountered user, and stored
    // in ice node class attributes - cts1, cts2, cts3, ...
    stylePrefix: 'cts',
    currentUser: {
      id: null,
      name: null
    },

    // Default change types are insert and delete. Plugins or outside apps should extend this
    // if they want to manage new change types. The changeType name is used as a primary
    // reference for ice nodes; the `alias`, is dropped in the class attribute and is the
    // primary method of identifying ice nodes; and `tag` is used for construction only.
    // Invoking `this.getCleanContent()` will remove all delete type nodes and remove the tags
    // for the other types, leaving the html content in place.
    changeTypes: {
      insertType: {
        tag: 'span',
        alias: 'ins',
        action: 'Inserted'
      },
      deleteType: {
        tag: 'span',
        alias: 'del',
        action: 'Deleted'
      }
    },

    // If `true`, setup event listeners on `this.element` and handle events - good option for a basic
    // setup without a text editor. Otherwise, when set to `false`, events need to be manually passed
    // to `handleEvent`, which is good for a text editor with an event callback handler, like tinymce.
    handleEvents: false,

    // Sets this.element with the contentEditable element
    contentEditable: true,

    // Switch for toggling track changes on/off - when `false` events will be ignored.
    isTracking: true,

    // NOT IMPLEMENTED - Selector for elements that will not get track changes
    noTrack: '.ice-no-track',

    // Selector for elements to avoid - move range before or after - similar handling to deletes
    avoid: '.ice-avoid',

    // Switch for whether paragraph breaks should be removed when the user is deleting over a
    // paragraph break while changes are tracked.
    mergeBlocks: true,

    // in case we have external way to initialize editor, just set next variable as false
    // and internal initializeEditor will be skipped
    runInitializeEditor: true,

    // custom function to handle delete of empty blocks (delete and forwared delete)
    customDeleteHandler: function(range, direction) {}
  };

  InlineChangeEditor = function (options) {

    // Data structure for modelling changes in the element according to the following model:
    //  [changeid] => {`type`, `time`, `userid`, `username`}
    this._changes = {};

    options || (options = {});
    if (!options.element) throw Error("`options.element` must be defined for ice construction.");

    ice.dom.extend(true, this, defaults, options);

    this.pluginsManager = new ice.IcePluginManager(this);
    if (options.plugins) this.pluginsManager.usePlugins('ice-init', options.plugins);
  };

  InlineChangeEditor.prototype = {
    // Tracks all of the styles for users according to the following model:
    //  [userId] => styleId; where style is "this.stylePrefix" + "this.uniqueStyleIndex"
    _userStyles: {},
    _styles: {},

    // Incremented for each new user and appended to they style prefix, and dropped in the
    // ice node class attribute.
    _uniqueStyleIndex: 0,

    _browserType: null,

    // One change may create multiple ice nodes, so this keeps track of the current batch id.
    _batchChangeid: null,

    // Incremented for each new change, dropped in the changeIdAttribute.
    _uniqueIDIndex: 1,

    // Temporary bookmark tags for deletes, when delete placeholding is active.
    _delBookmark: 'tempdel',
    isPlaceHoldingDeletes: false,

    /**
     * Turns on change tracking - sets up events, if needed, and initializes the environment,
     * range, and editor.
     */
    startTracking: function () {
      this.element.setAttribute('contentEditable', this.contentEditable);

      // If we are handling events setup the delegate to handle various events on `this.element`.
      if (this.handleEvents) {
        var self = this;
        ice.dom.bind(self.element, 'keyup.ice keydown.ice keypress.ice mousedown.ice mouseup.ice', function (e) {
          return self.handleEvent(e);
        });
      }

      if (this.runInitializeEditor)
        this.initializeEditor();

      this.initializeEnvironment();
      this.findTrackTags();
      this.initializeRange();

      this.pluginsManager.fireEnabled(this.element);
      return this;
    },

    /**
     * Removes contenteditability and stops event handling.
     */
    stopTracking: function () {
      this.element.setAttribute('contentEditable', !this.contentEditable);

      // If we are handling events setup the delegate to handle various events on `this.element`.
      if (this.handleEvents) {
        var self = this;
        ice.dom.unbind(self.element, 'keyup.ice keydown.ice keypress.ice mousedown.ice mouseup.ice');
      }

      this.pluginsManager.fireDisabled(this.element);
      return this;
    },

    /**
     * Initializes the `env` object with pointers to key objects of the page.
     */
    initializeEnvironment: function () {
      this.env || (this.env = {});
      this.env.element = this.element;
      this.env.document = this.element.ownerDocument;
      this.env.window = this.env.document.defaultView || this.env.document.parentWindow || window;
      this.env.frame = this.env.window.frameElement;
      this.env.selection = this.selection = new ice.Selection(this.env);
      // Hack for using custom tags in IE 8/7
      this.env.document.createElement(this.changeTypes.insertType.tag);
      this.env.document.createElement(this.changeTypes.deleteType.tag);
    },

    /**
     * Initializes the internal range object and sets focus to the editing element.
     */
    initializeRange: function () {
      var range = this.selection.createRange();
      range.setStart(ice.dom.find(this.element, this.blockEls.join(', '))[0], 0);
      range.collapse(true);
      this.selection.addRange(range);
      if (this.env.frame) this.env.frame.contentWindow.focus();
      else this.element.focus();
    },

    /**
     * Initializes the content in the editor - cleans non-block nodes found between blocks.
     */
    initializeEditor: function () {
      // Clean the element html body - add an empty block if there is no body, or remove any
      // content between elements.
      var body = this.env.document.createElement('div');
      if (this.element.childNodes.length) {
        body.innerHTML = this.element.innerHTML;
        ice.dom.removeWhitespace(body);
        if (body.innerHTML === '') body.appendChild(ice.dom.create('<' + this.blockEl + ' ><br/></' + this.blockEl + '>'));
      } else {
        body.appendChild(ice.dom.create('<' + this.blockEl + ' ><br/></' + this.blockEl + '>'));
      }
      if (this.element.innerHTML != body.innerHTML) {
        this.element.innerHTML = body.innerHTML;
      }

    },

    /*
     * Updates the list of changes to include all track tags found inside the element.
     */
    findTrackTags: function () {

      // Grab class for each changeType
      var self = this, changeTypeClasses = [];
      for (var changeType in this.changeTypes) {
        changeTypeClasses.push(this._getIceNodeClass(changeType));
      }

      ice.dom.each(ice.dom.find(this.element, '.' + changeTypeClasses.join(', .')), function (i, el) {
        var styleIndex = 0;
        var ctnType = '';
        var classList = el.className.split(' ');
        for (var i = 0; i < classList.length; i++) {
          var styleReg = new RegExp(self.stylePrefix + '-(\\d+)').exec(classList[i]);
          if (styleReg) styleIndex = styleReg[1];
          var ctnReg = new RegExp('(' + changeTypeClasses.join('|') + ')').exec(classList[i]);
          if (ctnReg) ctnType = self._getChangeTypeFromAlias(ctnReg[1]);
        }
        var userid = ice.dom.attr(el, self.userIdAttribute);
        self.setUserStyle(userid, Number(styleIndex));
        var changeid = ice.dom.attr(el, self.changeIdAttribute);
        self._changes[changeid] = {
          type: ctnType,
          userid: userid,
          username: ice.dom.attr(el, self.userNameAttribute),
          time: ice.dom.attr(el, self.timeAttribute)
        };
      });
    },

    /**
     * Turn on change tracking and event handling.
     */
    enableChangeTracking: function () {
      this.isTracking = true;
      this.pluginsManager.fireEnabled(this.element);
    },

    /**
     * Turn off change tracking and event handling.
     */
    disableChangeTracking: function () {
      this.isTracking = false;
      this.pluginsManager.fireDisabled(this.element);
    },

    /**
     * Set the user to be tracked. A user object has the following properties:
     * {`id`, `name`}
     */
    setCurrentUser: function (user) {
      this.currentUser = user;
    },

    /**
     * If tracking is on, handles event e when it is one of the following types:
     * mouseup, mousedown, keypress, keydown, and keyup. Each event type is
     * propagated to all of the plugins. Prevents default handling if the event
     * was fully handled.
     */
    handleEvent: function (e) {
      if (!this.isTracking) return;
      if (e.type == 'mouseup') {
        var self = this;
        setTimeout(function () {
          self.mouseUp(e);
        }, 200);
      } else if (e.type == 'mousedown') {
        return this.mouseDown(e);
      } else if (e.type == 'keypress') {
        var needsToBubble = this.keyPress(e);
        if (!needsToBubble) e.preventDefault();
        return needsToBubble;
      } else if (e.type == 'keydown') {
        var needsToBubble = this.keyDown(e);
        if (!needsToBubble) e.preventDefault();
        return needsToBubble;
      } else if (e.type == 'keyup') {
        this.pluginsManager.fireCaretUpdated();
      }
    },
  visible: function(el) {
    if (el.nodeType === ice.dom.TEXT_NODE) el = el.parentNode;
    if (!el) return false;

    var rect = el.getBoundingClientRect();
    return (rect.top > 0 && rect.left > 0);
  },

    /**
     * Returns a tracking tag for the given `changeType`, with the optional `childNode` appended.
     */
    createIceNode: function (changeType, childNode) {
      var node = this.env.document.createElement(this.changeTypes[changeType].tag);
      ice.dom.addClass(node, this._getIceNodeClass(changeType));

      node.appendChild(childNode ? childNode : this.env.document.createTextNode(''));
      this.addChange(this.changeTypes[changeType].alias, [node]);

      this.pluginsManager.fireNodeCreated(node, {
        'action': this.changeTypes[changeType].action
      });
      return node;
    },

    /**
     * Inserts the given string/node into the given range with tracking tags, collapsing (deleting)
     * the range first if needed. If range is undefined, then the range from the Selection object
     * is used. If the range is in a parent delete node, then the range is positioned after the delete.
     */
    insert: function (node, range) {
      // If the node is not defined, then we need to insert an
      // invisible space and force propagation to the browser.
      var isPropagating = !node;
      node || (node = '\uFEFF');

      if (range) this.selection.addRange(range);
      else range = this.getCurrentRange();

      if (typeof node === "string") node = document.createTextNode(node);

      // If we have any nodes selected, then we want to delete them before inserting the new text.
      if (!range.collapsed) {
        this.deleteContents();
        // Update the range
        range = this.getCurrentRange();
        if (range.startContainer === range.endContainer && this.element === range.startContainer) {
          // The whole editable element is selected. Need to remove everything and init its contents.
          ice.dom.empty(this.element);
          var firstSelectable = range.getLastSelectableChild(this.element);
          range.setStartAfter(firstSelectable);
          range.collapse(true);
        }
      }
      // If we are in a non-tracking/void element, move the range to the end/outside.
      this._moveRangeToValidTrackingPos(range);

      var changeid = this.startBatchChange();
      // Send a dummy node to be inserted, if node is undefined
      this._insertNode(node, range, isPropagating);
      this.pluginsManager.fireNodeInserted(node, range);
      this.endBatchChange(changeid);
      return isPropagating;
    },

    /**
     * This command will drop placeholders in place of delete tags in the element
     * body and store references in the `_deletes` array to the original delete nodes.
     *
     * A placeholder tag is of the following structure:
     *   <tempdel data-allocation="[NUM]" />
     * Where [NUM] is the referenced allocation in the `_deletes` array where the
     * original delete node is stored.
     */
    placeholdDeletes: function () {
      var self = this;
      if (this.isPlaceholdingDeletes) {
        this.revertDeletePlaceholders();
      }
      this.isPlaceholdingDeletes = true;
      this._deletes = [];
      var deleteSelector = '.' + this._getIceNodeClass('deleteType');
      ice.dom.each(ice.dom.find(this.element, deleteSelector), function (i, el) {
        self._deletes.push(ice.dom.cloneNode(el));
        ice.dom.replaceWith(el, '<' + self._delBookmark + ' data-allocation="' + (self._deletes.length - 1) + '"/>');
      });
      return true;
    },

    /**
     * Replaces all delete placeholders in the element body with the referenced
     * delete nodes in the `_deletes` array.
     *
     * A placeholder tag is of the following structure:
     *   <tempdel data-allocation="[NUM]" />
     * Where [NUM] is the referenced allocation in the `_deletes` array where the
     * original delete node is stored.
     */
    revertDeletePlaceholders: function () {
      var self = this;
      if (!this.isPlaceholdingDeletes) {
        return false;
      }
      ice.dom.each(this._deletes, function (i, el) {
        ice.dom.find(self.element, self._delBookmark + '[data-allocation=' + i + ']').replaceWith(el);
      });
      this.isPlaceholdingDeletes = false;
      return true;
    },
    /**
     * Deletes the contents in the given range or the range from the Selection object. If the range
     * is not collapsed, then a selection delete is handled; otherwise, it deletes one character
     * to the left or right if the right parameter is false or true, respectively.
     *
     * @return true if deletion was handled.
     */
    deleteContents: function (right, range) {
      var prevent = true;
      var browser = ice.dom.browser();

      if (range) {
        this.selection.addRange(range);
      } else {
        range = this.getCurrentRange();
      }

      var changeid = this.startBatchChange(this.changeTypes['deleteType'].alias);
      if (range.collapsed === false) {
        if (this._currentUserIceNode(range.startContainer.parentNode)) {
          // when it comes to same user insertNode, just let the native delete
          // or the customDeleteHandler works, setting prevent as false
          var insertNode = this.getIceNode(range.startContainer, 'insertType');
          if (insertNode) prevent = false;
          else this._deleteSelection(range);
        } else {
          this._deleteSelection(range);
          if(browser["type"] === "mozilla"){
            if(range.startContainer.parentNode.previousSibling){
              range.setEnd(range.startContainer.parentNode.previousSibling, 0);
              range.moveEnd(ice.dom.CHARACTER_UNIT, ice.dom.getNodeCharacterLength(range.endContainer));
            } else {
              range.setEndAfter(range.startContainer.parentNode);
            }
            range.collapse(false);
          } else {
            if(!this.visible(range.endContainer)){
              range.setEnd(range.endContainer, range.endOffset - 1);
              range.collapse(false);
            }
          }
        }
      } else {
        if (right) {
          // when delete inside of insert tracking tag, we let the native delete work or
          // use the customDeleteHandler function to avoid sending the cursor to the
          // start of the insertTracking tag
          var ctNode = this.getIceNode(range.startContainer, 'insertType');
          var inCurrentUserInsert = this._currentUserIceNode(ctNode);

          if (ctNode && inCurrentUserInsert){
            prevent = false;
          } else {
            // RIGHT DELETE
            if (browser["type"] === "mozilla") {
              prevent = this._deleteRight(range);
              // Handling track change show/hide
              if(!this.visible(range.endContainer)){
                if(range.endContainer.parentNode.nextSibling){
                  // range.setEnd(range.endContainer.parentNode.nextSibling, 0);
                  range.setEndBefore(range.endContainer.parentNode.nextSibling);
                } else {
                  range.setEndAfter(range.endContainer);
                }
                range.collapse(false);
              }
            }
            else {
              // Calibrate Cursor before deleting
              if (range.endOffset === ice.dom.getNodeCharacterLength(range.endContainer)){
                var next = range.startContainer.nextSibling;
                if (ice.dom.is(next,  '.' + this._getIceNodeClass('deleteType'))) {
                  while(next){
                    if (ice.dom.is(next,  '.' + this._getIceNodeClass('deleteType'))) {
                      next = next.nextSibling;
                      continue;
                    }
                    range.setStart(next, 0);
                    range.collapse(true);
                    break;
                  }
                }
              }

              // Delete
              prevent = this._deleteRight(range);

              // Calibrate Cursor after deleting
              if (!this.visible(range.endContainer)) {
                if (ice.dom.is(range.endContainer.parentNode,  '.' + this._getIceNodeClass('insertType') + ', .' + this._getIceNodeClass('deleteType'))) {
                  //            range.setStart(range.endContainer.parentNode.nextSibling, 0);
                  range.setStartAfter(range.endContainer.parentNode);
                  range.collapse(true);
                }
              }
            }
          }
        }
        else {
          // LEFT DELETE
          if(browser["type"] === "mozilla"){
            prevent = this._deleteLeft(range);
            // Handling track change show/hide
            if(!this.visible(range.startContainer)){
              if(range.startContainer.parentNode.previousSibling){
                range.setEnd(range.startContainer.parentNode.previousSibling, 0);
              } else {
                range.setEnd(range.startContainer.parentNode, 0);
              }
              range.moveEnd(ice.dom.CHARACTER_UNIT, ice.dom.getNodeCharacterLength(range.endContainer));
              range.collapse(false);
            }
          }
          else {
            if(!this.visible(range.startContainer)){
              if(range.endOffset === ice.dom.getNodeCharacterLength(range.endContainer)){
                var prev = range.startContainer.previousSibling;
                if (ice.dom.is(prev,  '.' + this._getIceNodeClass('deleteType'))) {
                  while(prev){
                    if (ice.dom.is(prev,  '.' + this._getIceNodeClass('deleteType'))) {
                      prev = prev.prevSibling;
                      continue;
                    }
                    range.setEndBefore(prev.nextSibling, 0);
                    range.collapse(false);
                    break;
                  }
                }
              }
            }
            prevent = this._deleteLeft(range);
          }
        }
      }

      if (prevent === false) {
        // call custom function to handle delete
        var direction = right ? 'right' : 'left';
        this.customDeleteHandler(range, direction);
      }

      this.selection.addRange(range);
      this.endBatchChange(changeid);
      return prevent;
    },

    /**
     * Returns the changes - a hash of objects with the following properties:
     * [changeid] => {`type`, `time`, `userid`, `username`}
     */
    getChanges: function () {
      return this._changes;
    },

    /**
     * Returns an array with the user ids who made the changes
     */
    getChangeUserids: function () {
      var result = [];
      var keys = Object.keys(this._changes);

      for (var key in keys)
      result.push(this._changes[keys[key]].userid);

      return result.sort().filter(function (el, i, a) {
        if (i == a.indexOf(el)) return 1;
        return 0;
      });
    },

    /**
     * Returns the html contents for the tracked element.
     */
    getElementContent: function () {
      return this.element.innerHTML;
    },

    /**
     * Returns the html contents, without tracking tags, for `this.element` or
     * the optional `body` param which can be of either type string or node.
     * Delete tags, and their html content, are completely removed; all other
     * change type tags are removed, leaving the html content in place. After
     * cleaning, the optional `callback` is executed, which should further
     * modify and return the element body.
     *
     * prepare gets run before the body is cleaned by ice.
     */
    getCleanContent: function (body, callback, prepare) {
      var classList = '';
      var self = this;
      ice.dom.each(this.changeTypes, function (type, i) {
        if (type != 'deleteType') {
          if (i > 0) classList += ',';
          classList += '.' + self._getIceNodeClass(type);
        }
      });
      if (body) {
        if (typeof body === 'string') body = ice.dom.create('<div>' + body + '</div>');
        else body = ice.dom.cloneNode(body, false)[0];
      } else {
        body = ice.dom.cloneNode(this.element, false)[0];
      }
      body = prepare ? prepare.call(this, body) : body;
      var changes = ice.dom.find(body, classList);
      ice.dom.each(changes, function (el, i) {
        ice.dom.replaceWith(this, ice.dom.contents(this));
      });
      var deletes = ice.dom.find(body, '.' + this._getIceNodeClass('deleteType'));
      ice.dom.remove(deletes);

      body = callback ? callback.call(this, body) : body;

      return body.innerHTML;
    },

    /**
     * Accepts all changes in the element body - removes delete nodes, and removes outer
     * insert tags keeping the inner content in place.
     */
    acceptAll: function () {
      this.element.innerHTML = this.getCleanContent();
    },

    /**
     * Rejects all changes in the element body - removes insert nodes, and removes outer
     * delete tags keeping the inner content in place.*
     */
    rejectAll: function () {
      var insSel = '.' + this._getIceNodeClass('insertType');
      var delSel = '.' + this._getIceNodeClass('deleteType');

      ice.dom.remove(ice.dom.find(this.element, insSel));
      ice.dom.each(ice.dom.find(this.element, delSel), function (i, el) {
        ice.dom.replaceWith(el, ice.dom.contents(el));
      });
    },

    /**
     * Accepts the change at the given, or first tracking parent node of, `node`.  If
     * `node` is undefined then the startContainer of the current collapsed range will be used.
     * In the case of insert, inner content will be used to replace the containing tag; and in
     * the case of delete, the node will be removed.
     */
    acceptChange: function (node) {
      this.acceptRejectChange(node, true);
    },

    /**
     * Rejects the change at the given, or first tracking parent node of, `node`.  If
     * `node` is undefined then the startContainer of the current collapsed range will be used.
     * In the case of delete, inner content will be used to replace the containing tag; and in
     * the case of insert, the node will be removed.
     */
    rejectChange: function (node) {
      this.acceptRejectChange(node, false);
    },

    /**
     * Handles accepting or rejecting tracking changes
     */
    acceptRejectChange: function (node, isAccept) {
      var delSel, insSel, selector, removeSel, replaceSel, trackNode, changes, dom = ice.dom;

      if (!node) {
        var range = this.getCurrentRange();
        if (!range.collapsed) return;
        else node = range.startContainer;
      }

      delSel = removeSel = '.' + this._getIceNodeClass('deleteType');
      insSel = replaceSel = '.' + this._getIceNodeClass('insertType');
      selector = delSel + ',' + insSel;
      trackNode = dom.getNode(node, selector);
      // Some changes are done in batches so there may be other tracking
      // nodes with the same `changeIdAttribute` batch number.
      changes = dom.find(this.element, '[' + this.changeIdAttribute + '=' + dom.attr(trackNode, this.changeIdAttribute) + ']');

      if (!isAccept) {
        removeSel = insSel;
        replaceSel = delSel;
      }

      if (ice.dom.is(trackNode, replaceSel)) {
        dom.each(changes, function (i, node) {
          dom.replaceWith(node, ice.dom.contents(node));
        });
      } else if (dom.is(trackNode, removeSel)) {
        dom.remove(changes);
      }
    },

    /**
     * Returns true if the given `node`, or the current collapsed range is in a tracking
     * node; otherwise, false.
     */
    isInsideChange: function (node) {
      var selector = '.' + this._getIceNodeClass('insertType') + ', .' + this._getIceNodeClass('deleteType');
      if (!node) {
        range = this.getCurrentRange();
        if (!range.collapsed) return false;
        else node = range.startContainer;
      }
      return !!ice.dom.getNode(node, selector);
    },

    /**
     * Add a new change tracking typeName with the given tag and alias.
     */
    addChangeType: function (typeName, tag, alias, action) {
      var changeType = {
        tag: tag,
        alias: alias
      };

      if (action) changeType.action = action;

      this.changeTypes[typeName] = changeType;
    },

    /**
     * Returns this `node` or the first parent tracking node with the given `changeType`.
     */
    getIceNode: function (node, changeType) {
      var selector = '.' + this._getIceNodeClass(changeType);
      return ice.dom.getNode(node, selector);
    },

    /**
     * Sets the given `range` to the first position, to the right, where it is outside of
     * void elements.
     */
    _moveRangeToValidTrackingPos: function (range) {
      var onEdge = false;
      var voidEl = this._getVoidElement(range.endContainer);
      while (voidEl) {
        // Move end of range to position it inside of any potential adjacent containers
        // E.G.:  test|<em>text</em>  ->  test<em>|text</em>
        try {
          range.moveEnd(ice.dom.CHARACTER_UNIT, 1);
          range.moveEnd(ice.dom.CHARACTER_UNIT, -1);
        } catch (e) {
          // Moving outside of the element and nothing is left on the page
          onEdge = true;
        }
        if (onEdge || ice.dom.onBlockBoundary(range.endContainer, range.startContainer, this.blockEls)) {
          range.setStartAfter(voidEl);
          range.collapse(true);
          break;
        }
        voidEl = this._getVoidElement(range.endContainer);
        if (voidEl) {
          range.setEnd(range.endContainer, 0);
      range.moveEnd(ice.dom.CHARACTER_UNIT, ice.dom.getNodeCharacterLength(range.endContainer));
          range.collapse();
        } else {
          range.setStart(range.endContainer, 0);
          range.collapse(true);
        }
      }
    },

    /**
     * Returns the given `node` or the first parent node that matches against the list of no track elements.
     */
    _getNoTrackElement: function (node) {
      var noTrackSelector = this._getNoTrackSelector();
      var parent = ice.dom.is(node, noTrackSelector) ? node : (ice.dom.parents(node, noTrackSelector)[0] || null);
      return parent;
    },

    /**
     * Returns a selector for not tracking changes
     */
    _getNoTrackSelector: function () {
      return this.noTrack;
    },

    /**
     * Returns the given `node` or the first parent node that matches against the list of void elements.
     */
    _getVoidElement: function (node) {
      var voidSelector = this._getVoidElSelector();
      return ice.dom.is(node, voidSelector) ? node : (ice.dom.parents(node, voidSelector)[0] || null);
    },

    /**
     * Returns a combined selector for delete and void elements.
     */
    _getVoidElSelector: function () {
      return '.' + this._getIceNodeClass('deleteType') + ',' + this.avoid;
    },

    /**
     * Returns true if node has a user id attribute that matches the current user id.
     */
    _currentUserIceNode: function (node) {
      return ice.dom.attr(node, this.userIdAttribute) == this.currentUser.id;
    },

    /**
     * With the given alias, searches the changeTypes objects and returns the
     * associated key for the alias.
     */
    _getChangeTypeFromAlias: function (alias) {
      var type, ctnType = null;
      for (type in this.changeTypes) {
        if (this.changeTypes.hasOwnProperty(type)) {
          if (this.changeTypes[type].alias == alias) {
            ctnType = type;
          }
        }
      }

      return ctnType;
    },

    _getIceNodeClass: function (changeType) {
      return this.attrValuePrefix + this.changeTypes[changeType].alias;
    },

    getUserStyle: function (userid) {
      var styleIndex = null;
      if (this._userStyles[userid]) styleIndex = this._userStyles[userid];
      else styleIndex = this.setUserStyle(userid, this.getNewStyleId());
      return styleIndex;
    },

    setUserStyle: function (userid, styleIndex) {
      var style = this.stylePrefix + '-' + styleIndex;
      if (!this._styles[styleIndex]) this._styles[styleIndex] = true;
      return this._userStyles[userid] = style;
    },

    getNewStyleId: function () {
      var id = ++this._uniqueStyleIndex;
      if (this._styles[id]) {
        // Dupe.. create another..
        return this.getNewStyleId();
      } else {
        this._styles[id] = true;
        return id;
      }
    },

    addChange: function (ctnType, ctNodes) {
      var changeid = this._batchChangeid || this.getNewChangeId();
      if (!this._changes[changeid]) {
        // Create the change object.
        this._changes[changeid] = {
          type: this._getChangeTypeFromAlias(ctnType),
          time: (new Date()).getTime(),
          userid: this.currentUser.id,
          username: this.currentUser.name
        };
      }
      var self = this;
      ice.dom.foreach(ctNodes, function (i) {
        self.addNodeToChange(changeid, ctNodes[i]);
      });

      return changeid;
    },

    /**
     * Adds tracking attributes from the change with changeid to the ctNode.
     * @param changeid Id of an existing change.
     * @param ctNode The element to add for the change.
     */
    addNodeToChange: function (changeid, ctNode) {
      if (this._batchChangeid !== null) changeid = this._batchChangeid;

      var change = this.getChange(changeid);

      if (!ctNode.getAttribute(this.changeIdAttribute)) ctNode.setAttribute(this.changeIdAttribute, changeid);

      if (!ctNode.getAttribute(this.userIdAttribute)) ctNode.setAttribute(this.userIdAttribute, change.userid);

      if (!ctNode.getAttribute(this.userNameAttribute)) ctNode.setAttribute(this.userNameAttribute, change.username);

      if (!ctNode.getAttribute(this.timeAttribute)) ctNode.setAttribute(this.timeAttribute, change.time);

      if (!ice.dom.hasClass(ctNode, this._getIceNodeClass(change.type))) ice.dom.addClass(ctNode, this._getIceNodeClass(change.type));

      var style = this.getUserStyle(change.userid);
      if (!ice.dom.hasClass(ctNode, style)) ice.dom.addClass(ctNode, style);
    },

    getChange: function (changeid) {
      var change = null;
      if (this._changes[changeid]) {
        change = this._changes[changeid];
      }
      return change;
    },

    getNewChangeId: function () {
      var id = ++this._uniqueIDIndex;
      if (this._changes[id]) {
        // Dupe.. create another..
        id = this.getNewChangeId();
      }
      return id;
    },

    startBatchChange: function () {
      this._batchChangeid = this.getNewChangeId();
      return this._batchChangeid;
    },

    endBatchChange: function (changeid) {
      if (changeid !== this._batchChangeid) return;
      this._batchChangeid = null;
    },

    getCurrentRange: function () {
      return this.selection.getRangeAt(0);
    },

    _insertNode: function (node, range, insertingDummy) {
      var origNode = node;
      if (!ice.dom.isBlockElement(range.startContainer) && !ice.dom.canContainTextElement(ice.dom.getBlockParent(range.startContainer, this.element)) && range.startContainer.previousSibling) {
        range.setStart(range.startContainer.previousSibling, 0);

      }
      var startContainer = range.startContainer;
      var parentBlock = ice.dom.isBlockElement(range.startContainer) && range.startContainer || ice.dom.getBlockParent(range.startContainer, this.element) || null;
      if (parentBlock === this.element) {
        var firstPar = document.createElement(this.blockEl);
        parentBlock.appendChild(firstPar);
        range.setStart(firstPar, 0);
        range.collapse();
        return this._insertNode(node, range, insertingDummy);
      }
      if (ice.dom.hasNoTextOrStubContent(parentBlock)) {
        ice.dom.empty(parentBlock);
        ice.dom.append(parentBlock, '<br>');
        range.setStart(parentBlock, 0);
      }

      var ctNode = this.getIceNode(range.startContainer, 'insertType');
      var inCurrentUserInsert = this._currentUserIceNode(ctNode);

      // Do nothing, let this bubble-up to insertion handler.
      if (insertingDummy && inCurrentUserInsert) return;
      // If we aren't in an insert node which belongs to the current user, then create a new ins node
      else if (!inCurrentUserInsert) node = this.createIceNode('insertType', node);

      range.insertNode(node);
      range.setEnd(node, 1);

      if (insertingDummy) {
        // Create a selection of the dummy character we inserted
        // which will be removed after it bubbles up to the final handler.
        range.setStart(node, 0);
      } else {
        range.collapse();
      }

      this.selection.addRange(range);
    },

    _handleVoidEl: function(el, range) {
      // If `el` is or is in a void element, but not a delete
      // then collapse the `range` and return `true`.
      var voidEl = this._getVoidElement(el);
      if (voidEl && !this.getIceNode(voidEl, 'deleteType')) {
        range.collapse(true);
        return true;
      }
      return false;
    },

    _deleteSelection: function (range) {

      // Bookmark the range and get elements between.
      var bookmark = new ice.Bookmark(this.env, range),
        elements = ice.dom.getElementsBetween(bookmark.start, bookmark.end),
        b1 = ice.dom.parents(range.startContainer, this.blockEls.join(', '))[0],
        b2 = ice.dom.parents(range.endContainer, this.blockEls.join(', '))[0],
        betweenBlocks = new Array();

      for (var i = 0; i < elements.length; i++) {
        var elem = elements[i];
        if (ice.dom.isBlockElement(elem)) {
          betweenBlocks.push(elem);
          if (!ice.dom.canContainTextElement(elem)) {
            // Ignore containers that are not supposed to contain text. Check children instead.
            for (var k = 0; k < elem.childNodes.length; k++) {
              elements.push(elem.childNodes[k]);
            }
            continue;
          }
        }
        // Ignore empty space nodes
        if (elem.nodeType === ice.dom.TEXT_NODE && ice.dom.getNodeTextContent(elem).length === 0) continue;

        if (!this._getVoidElement(elem)) {
          // If the element is not a text or stub node, go deeper and check the children.
          if (elem.nodeType !== ice.dom.TEXT_NODE) {
            // Browsers like to insert breaks into empty paragraphs - remove them
            if (ice.dom.BREAK_ELEMENT == ice.dom.getTagName(elem)) {
              continue;
            }

            if (ice.dom.isStubElement(elem)) {
              this._addNodeTracking(elem, false, true);
              continue;
            }
            if (ice.dom.hasNoTextOrStubContent(elem)) {
              ice.dom.remove(elem);
            }

            for (j = 0; j < elem.childNodes.length; j++) {
              var child = elem.childNodes[j];
              elements.push(child);
            }
            continue;
          }
          var parentBlock = ice.dom.getBlockParent(elem);
          this._addNodeTracking(elem, false, true, true);
          if (ice.dom.hasNoTextOrStubContent(parentBlock)) {
            ice.dom.remove(parentBlock);
          }
        }
      }

      if (this.mergeBlocks && b1 !== b2) {
        while (betweenBlocks.length)
          ice.dom.mergeContainers(betweenBlocks.shift(), b1);
        ice.dom.removeBRFromChild(b2);
        ice.dom.removeBRFromChild(b1);
        ice.dom.mergeContainers(b2, b1);
      }

      bookmark.selectBookmark();
      //  range.collapse(false);
      range.collapse(true);
    },

    // Delete
    _deleteRight: function (range) {

      var parentBlock = ice.dom.isBlockElement(range.startContainer) && range.startContainer || ice.dom.getBlockParent(range.startContainer, this.element) || null,
        isEmptyBlock = parentBlock ? (ice.dom.hasNoTextOrStubContent(parentBlock)) : false,
        nextBlock = parentBlock && ice.dom.getNextContentNode(parentBlock, this.element),
        nextBlockIsEmpty = nextBlock ? (ice.dom.hasNoTextOrStubContent(nextBlock)) : false,
        initialContainer = range.endContainer,
        initialOffset = range.endOffset,
        commonAncestor = range.commonAncestorContainer,
        nextContainer, returnValue;

      // If the current block is empty, let's recalibrate the caret
      // and then let the browser handle the delete/event.
      if (isEmptyBlock) {
        range.setEnd(nextBlock, 0);
        range.moveEnd(ice.dom.CHARACTER_UNIT, 1);
        range.moveEnd(ice.dom.CHARACTER_UNIT, -1);
        return false;
      }

      // Some bugs in Firefox and Webkit make the caret disappear out of text nodes, so we try to put them back in.
      if (commonAncestor.nodeType !== ice.dom.TEXT_NODE) {

        // If placed at the beginning of a container that cannot contain text, such as an ul element, place the caret at the beginning of the first item.
        if (initialOffset === 0 && ice.dom.isBlockElement(commonAncestor) && (!ice.dom.canContainTextElement(commonAncestor))) {
          var firstItem = commonAncestor.firstElementChild;
          if (firstItem) {
            range.setStart(firstItem, 0);
            range.collapse();
            return this._deleteRight(range);
          }
        }

        if (commonAncestor.childNodes.length > initialOffset) {
          var tempTextContainer = document.createTextNode(' ');
          commonAncestor.insertBefore(tempTextContainer, commonAncestor.childNodes[initialOffset]);
          if (!tempTextContainer) return false;
          range.setStart(tempTextContainer, 1);
          range.collapse(true);
          returnValue = this._deleteRight(range);
          ice.dom.remove(tempTextContainer);
          return returnValue;
        } else {
          nextContainer = ice.dom.getNextContentNode(commonAncestor, this.element);
          if (!nextContainer) return false;
          range.setEnd(nextContainer, 0);
          range.collapse();
          return this._deleteRight(range);
        }
      }

      // Move range to position the cursor on the inside of any adjacent container that it is going
      // to potentially delete into or after a stub element.  E.G.:  test|<em>text</em>  ->  test<em>|text</em> or
      // text1 |<img> text2 -> text1 <img>| text2

      // Merge blocks: If mergeBlocks is enabled, merge the previous and current block.
      range.moveEnd(ice.dom.CHARACTER_UNIT, 1);
      range.moveEnd(ice.dom.CHARACTER_UNIT, -1);

      // Handle cases of the caret is at the end of a container or placed directly in a block element
      if (initialOffset === initialContainer.data.length && (!ice.dom.hasNoTextOrStubContent(initialContainer))) {
        nextContainer = ice.dom.getNextNode(initialContainer, this.element);

        // If the next container is outside of ICE then do nothing.
        if (!nextContainer) {
          range.selectNodeContents(initialContainer);
          range.collapse();
          return false;
        }

        // If the next container is <br> element find the next node
        if (ice.dom.BREAK_ELEMENT == ice.dom.getTagName(nextContainer)) {
          nextContainer = ice.dom.getNextNode(nextContainer, this.element);
        }
        // If the next container is a text node, look at the parent node instead.
        if (nextContainer.nodeType === ice.dom.TEXT_NODE) {
          nextContainer = nextContainer.parentNode;
        }

        // If the next container is non-editable, enclose it with a delete ice node and add an empty text node after it to position the caret.
        if (!nextContainer.isContentEditable) {
          returnValue = this._addNodeTracking(nextContainer, false, false);
          var emptySpaceNode = document.createTextNode('');
          nextContainer.parentNode.insertBefore(emptySpaceNode, nextContainer.nextSibling);
          range.selectNode(emptySpaceNode);
          range.collapse(true);
          return returnValue;
        }

        if (this._handleVoidEl(nextContainer, range)) return true;

        // If the caret was placed directly before a stub element, enclose the element with a delete ice node.
        if (ice.dom.isChildOf(nextContainer, parentBlock) && ice.dom.isStubElement(nextContainer)) {
          return this._addNodeTracking(nextContainer, range, false);
        }

      }

      if (this._handleVoidEl(nextContainer, range)) return true;

      // If we are deleting into a no tracking containiner, then remove the content
      if (this._getNoTrackElement(range.endContainer.parentElement)) {
        range.deleteContents();
        return false;
      }

      if (ice.dom.isOnBlockBoundary(range.startContainer, range.endContainer, this.element)) {
        if (this.mergeBlocks && ice.dom.is(ice.dom.getBlockParent(nextContainer, this.element), this.blockEl)) {
          // Since the range is moved by character, it may have passed through empty blocks.
          // <p>text {RANGE.START}</p><p></p><p>{RANGE.END} text</p>
          if (nextBlock && nextBlock !== ice.dom.getBlockParent(range.endContainer, this.element)) {
            range.setEnd(nextBlock, 0);
          }
          // The browsers like to auto-insert breaks into empty paragraphs - remove them.
          var elements = ice.dom.getElementsBetween(range.startContainer, range.endContainer);
          for (var i = 0; i < elements.length; i++) {
            ice.dom.remove(elements[i]);
          }
          var startContainer = range.startContainer;
          var endContainer = range.endContainer;
          ice.dom.remove(ice.dom.find(startContainer, 'br'));
          ice.dom.remove(ice.dom.find(endContainer, 'br'));
          return ice.dom.mergeBlockWithSibling(range, ice.dom.getBlockParent(range.endContainer, this.element) || parentBlock);
        } else {
          // If the next block is empty, remove the next block.
          if (nextBlockIsEmpty) {
            ice.dom.remove(nextBlock);
            range.collapse(true);
            return true;
          }

          // Place the caret at the start of the next block.
          range.setStart(nextBlock, 0);
          range.collapse(true);
          return true;
        }
      }

      var entireTextNode = range.endContainer;
      var deletedCharacter = entireTextNode.splitText(range.endOffset);
      var remainingTextNode = deletedCharacter.splitText(1);

      return this._addNodeTracking(deletedCharacter, range, false);

    },

    // Backspace
    _deleteLeft: function (range) {

      var parentBlock = ice.dom.isBlockElement(range.startContainer) && range.startContainer || ice.dom.getBlockParent(range.startContainer, this.element) || null,
        isEmptyBlock = parentBlock ? ice.dom.hasNoTextOrStubContent(parentBlock) : false,
        prevBlock = parentBlock && ice.dom.getPrevContentNode(parentBlock, this.element), // || ice.dom.getBlockParent(parentBlock, this.element) || null,
        prevBlockIsEmpty = prevBlock ? ice.dom.hasNoTextOrStubContent(prevBlock) : false,
        initialContainer = range.startContainer,
        initialOffset = range.startOffset,
        commonAncestor = range.commonAncestorContainer,
        lastSelectable, prevContainer;

      // If the current block is empty, then let the browser handle the key/event.
      if (isEmptyBlock) return false;

      // Handle cases of the caret is at the start of a container or outside a text node
      if (initialOffset === 0 || commonAncestor.nodeType !== ice.dom.TEXT_NODE) {
        // If placed at the end of a container that cannot contain text, such as an ul element, place the caret at the end of the last item.
        if (ice.dom.isBlockElement(commonAncestor) && (!ice.dom.canContainTextElement(commonAncestor))) {
          if (initialOffset === 0) {
            var firstItem = commonAncestor.firstElementChild;
            if (firstItem) {
              range.setStart(firstItem, 0);
              range.collapse();
              return this._deleteLeft(range);
            }

          } else {
            var lastItem = commonAncestor.lastElementChild;
            if (lastItem) {

              lastSelectable = range.getLastSelectableChild(lastItem);
              if (lastSelectable) {
                range.setStart(lastSelectable, lastSelectable.data.length);
                range.collapse();
                return this._deleteLeft(range);
              }
            }
          }
        }
        if (initialOffset === 0) {
          prevContainer = ice.dom.getPrevContentNode(initialContainer, this.element);
        } else {
          var newOffset = initialOffset;
          var style;
          //      while(newOffset > 0){
          //        prevContainer = commonAncestor.childNodes[--newOffset];
          //        if(!ice.dom.hasClass(prevContainer, "del")) break;
          //        prevContainer = null;
          //      }
          prevContainer = commonAncestor.childNodes[initialOffset-1];
        }

        // If the previous container is outside of ICE then do nothing.
        if (!prevContainer) {
          return false;
        }
        // Firefox finds an ice node wrapped around an image instead of the image itself sometimes, so we make sure to look at the image instead.
        if (ice.dom.is(prevContainer,  '.' + this._getIceNodeClass('insertType') + ', .' + this._getIceNodeClass('deleteType')) && prevContainer.childNodes.length > 0 && prevContainer.lastChild) {
          prevContainer = prevContainer.lastChild;
        }

        // If the previous container is a text node, look at the parent node instead.
        if (prevContainer.nodeType === ice.dom.TEXT_NODE) {
          prevContainer = prevContainer.parentNode;
        }

        // If the previous container is non-editable, enclose it with a delete ice node and add an empty text node before it to position the caret.
        if (!prevContainer.isContentEditable) {
          var returnValue = this._addNodeTracking(prevContainer, false, true);
          var emptySpaceNode = document.createTextNode('');
          prevContainer.parentNode.insertBefore(emptySpaceNode, prevContainer);
          range.selectNode(emptySpaceNode);
          range.collapse(true);
          return returnValue;
        }

        if (this._handleVoidEl(prevContainer, range)) return true;

        // If the caret was placed directly after a stub element, enclose the element with a delete ice node.
        if (ice.dom.isStubElement(prevContainer) && ice.dom.isChildOf(prevContainer, parentBlock) || !prevContainer.isContentEditable) {
           return this._addNodeTracking(prevContainer, range, true);
        }

        // If the previous container is a stub element between blocks
        // then just delete and leave the range/cursor in place.
        if (ice.dom.isStubElement(prevContainer)) {
          ice.dom.remove(prevContainer);
          range.collapse(true);
          return false;
        }

        if (prevContainer !== parentBlock && !ice.dom.isChildOf(prevContainer, parentBlock)) {

          if (!ice.dom.canContainTextElement(prevContainer)) {
            prevContainer = prevContainer.lastElementChild;
          }
          // Before putting the caret into the last selectable child, lets see if the last element is a stub element. If it is, we need to put the caret there manually.
          if (prevContainer && prevContainer.lastChild && prevContainer.lastChild.nodeType !== ice.dom.TEXT_NODE && ice.dom.isStubElement(prevContainer.lastChild) && prevContainer.lastChild.tagName !== 'BR') {
            range.setStartAfter(prevContainer.lastChild);
            range.collapse(true);
            return true;
          }
          // Find the last selectable part of the prevContainer. If it exists, put the caret there.
          lastSelectable = range.getLastSelectableChild(prevContainer);

          if (lastSelectable && !ice.dom.isOnBlockBoundary(range.startContainer, lastSelectable, this.element)) {
            range.selectNodeContents(lastSelectable);
            range.collapse();
            return true;
          }
        }
      }

      // Firefox: If an image is at the start of the paragraph and the user has just deleted the image using backspace, an empty text node is created in the delete node before
      // the image, but the caret is placed with the image. We move the caret to the empty text node and execute deleteFromLeft again.
      if (initialOffset === 1 && !ice.dom.isBlockElement(commonAncestor) && range.startContainer.childNodes.length > 1 && range.startContainer.childNodes[0].nodeType === ice.dom.TEXT_NODE && range.startContainer.childNodes[0].data.length === 0) {
        range.setStart(range.startContainer, 0);
        return this._deleteLeft(range);
      }

      // Move range to position the cursor on the inside of any adjacent container that it is going
      // to potentially delete into or before a stub element.  E.G.: <em>text</em>| test  ->  <em>text|</em> test or
      // text1 <img>| text2 -> text1 |<img> text2
      range.moveStart(ice.dom.CHARACTER_UNIT, -1);
      range.moveStart(ice.dom.CHARACTER_UNIT, 1);

      // If we are deleting into a no tracking containiner, then remove the content
      if (this._getNoTrackElement(range.startContainer.parentElement)) {
        range.deleteContents();
        return false;
      }

      // Handles cases in which the caret is at the start of the block.
      if (ice.dom.isOnBlockBoundary(range.startContainer, range.endContainer, this.element)) {

        // If the previous block is empty, remove the previous block.
        if (prevBlockIsEmpty) {
          ice.dom.remove(prevBlock);
          range.collapse();
          return true;
        }

        // Merge blocks: If mergeBlocks is enabled, merge the previous and current block.
        if (this.mergeBlocks && ice.dom.is(ice.dom.getBlockParent(prevContainer, this.element), this.blockEl)) {
          // Since the range is moved by character, it may have passed through empty blocks.
          // <p>text {RANGE.START}</p><p></p><p>{RANGE.END} text</p>
          if (prevBlock && prevBlock !== ice.dom.getBlockParent(range.startContainer, this.element)) {
            range.setStart(prevBlock, prevBlock.childNodes.length);
          }
          // The browsers like to auto-insert breaks into empty paragraphs - remove them.
          var elements = ice.dom.getElementsBetween(range.startContainer, range.endContainer)
          for (var i = 0; i < elements.length; i++) {
            ice.dom.remove(elements[i]);
          }
          var startContainer = range.startContainer;
          var endContainer = range.endContainer;
          ice.dom.remove(ice.dom.find(startContainer, 'br'));
          ice.dom.remove(ice.dom.find(endContainer, 'br'));
          return ice.dom.mergeBlockWithSibling(range, ice.dom.getBlockParent(range.endContainer, this.element) || parentBlock);
        }

        // If the previous Block ends with a stub element, set the caret behind it.
        if (prevBlock && prevBlock.lastChild && ice.dom.isStubElement(prevBlock.lastChild)) {
          range.setStartAfter(prevBlock.lastChild);
          range.collapse(true);
          return true;
        }

        // Place the caret at the end of the previous block.
        lastSelectable = range.getLastSelectableChild(prevBlock);
        if (lastSelectable) {
          range.setStart(lastSelectable, lastSelectable.data.length);
          range.collapse(true);
        } else if (prevBlock) {
          range.setStart(prevBlock, prevBlock.childNodes.length);
          range.collapse(true);
        }

        return true;
      }

      var entireTextNode = range.startContainer;
      var deletedCharacter = entireTextNode.splitText(range.startOffset - 1);
      var remainingTextNode = deletedCharacter.splitText(1);

      return this._addNodeTracking(deletedCharacter, range, true);

    },

    // Marks text and other nodes for deletion
    _addNodeTracking: function (contentNode, range, moveLeft) {

      var contentAddNode = this.getIceNode(contentNode, 'insertType');

      if (contentAddNode && this._currentUserIceNode(contentAddNode)) {
        if (range && moveLeft) {
          range.selectNode(contentNode);
        }
        contentNode.parentNode.removeChild(contentNode);
        var cleanNode = ice.dom.cloneNode(contentAddNode);
        ice.dom.remove(ice.dom.find(cleanNode, '.iceBookmark'));
        // Remove a potential empty tracking container
        if (contentAddNode !== null && (ice.dom.hasNoTextOrStubContent(cleanNode[0]))) {
          var newstart = this.env.document.createTextNode('');
          ice.dom.insertBefore(contentAddNode, newstart);
          if (range) {
            range.setStart(newstart, 0);
            range.collapse(true);
          }
          ice.dom.replaceWith(contentAddNode, ice.dom.contents(contentAddNode));
        }

        return true;

      } else if (range && this.getIceNode(contentNode, 'deleteType')) {
        // It if the contentNode a text node, unite it with text nodes before and after it.
        contentNode.normalize();

        var found = false;
        if (moveLeft) {
          // Move to the left until there is valid sibling.
          var previousSibling = ice.dom.getPrevContentNode(contentNode, this.element);
          while (!found) {
            ctNode = this.getIceNode(previousSibling, 'deleteType');
            if (!ctNode) {
              found = true;
            } else {
              previousSibling = ice.dom.getPrevContentNode(previousSibling, this.element);
            }
          }
          if (previousSibling) {
            var lastSelectable = range.getLastSelectableChild(previousSibling);
            if (lastSelectable) {
              previousSibling = lastSelectable;
            }
            range.setStart(previousSibling, ice.dom.getNodeCharacterLength(previousSibling));
            range.collapse(true);
          }
          return true;
        } else {
          // Move the range to the right until there is valid sibling.

          var nextSibling = ice.dom.getNextContentNode(contentNode, this.element);
          while (!found) {
            ctNode = this.getIceNode(nextSibling, 'deleteType');
            if (!ctNode) {
              found = true;
            } else {
              nextSibling = ice.dom.getNextContentNode(nextSibling, this.element);
            }
          }

          if (nextSibling) {
            range.selectNodeContents(nextSibling);
            range.collapse(true);
          }
          return true;
        }

      }
      // Webkit likes to insert empty text nodes next to elements. We remove them here.
      if (contentNode.previousSibling && contentNode.previousSibling.nodeType === ice.dom.TEXT_NODE && contentNode.previousSibling.length === 0) {
        contentNode.parentNode.removeChild(contentNode.previousSibling);
      }
      if (contentNode.nextSibling && contentNode.nextSibling.nodeType === ice.dom.TEXT_NODE && contentNode.nextSibling.length === 0) {
        contentNode.parentNode.removeChild(contentNode.nextSibling);
      }
      var prevDelNode = this.getIceNode(contentNode.previousSibling, 'deleteType');
      var nextDelNode = this.getIceNode(contentNode.nextSibling, 'deleteType');
      var ctNode;

      if (prevDelNode && this._currentUserIceNode(prevDelNode)) {
        ctNode = prevDelNode;
        ctNode.appendChild(contentNode);
        if (nextDelNode && this._currentUserIceNode(nextDelNode)) {
          var nextDelContents = ice.dom.extractContent(nextDelNode);
          ice.dom.append(ctNode, nextDelContents);
          nextDelNode.parentNode.removeChild(nextDelNode);
        }
      } else if (nextDelNode && this._currentUserIceNode(nextDelNode)) {
        ctNode = nextDelNode;
        ctNode.insertBefore(contentNode, ctNode.firstChild);
      } else {
        ctNode = this.createIceNode('deleteType');
        contentNode.parentNode.insertBefore(ctNode, contentNode);
        ctNode.appendChild(contentNode);
      }

      if (range) {
        if (ice.dom.isStubElement(contentNode)) {
          range.selectNode(contentNode);
        } else {
          range.selectNodeContents(contentNode);
        }
        if (moveLeft) {
          range.collapse(true);
        } else {
          range.collapse();
        }
        contentNode.normalize();
      }
      return true;

    },


    /**
     * Handles arrow, delete key events, and others.
     *
     * @param {event} e The event object.
     * return {void|boolean} Returns false if default event needs to be blocked.
     */
    _handleAncillaryKey: function (e) {
      var key = e.keyCode ? e.keyCode : e.which;
      var browser = ice.dom.browser();
      var preventDefault = true;
      var shiftKey = e.shiftKey;
      var self = this;
      var range = self.getCurrentRange();
      switch (key) {
        case ice.dom.DOM_VK_DELETE:
          preventDefault = this.deleteContents();
          this.pluginsManager.fireKeyPressed(e);
          break;
        case 46:
          // Key 46 is the DELETE key.
          preventDefault = this.deleteContents(true);
          this.pluginsManager.fireKeyPressed(e);
          break;

        /************************************************************************************/
        /** BEGIN: Handling of caret movements inside hidden .ins/.del elements on Firefox **/
        /**  *Fix for carets getting stuck in .del elements when track changes are hidden  **/
        case ice.dom.DOM_VK_DOWN:
        case ice.dom.DOM_VK_UP:
        case ice.dom.DOM_VK_LEFT:
          this.pluginsManager.fireCaretPositioned();
          if (browser["type"] === "mozilla") {
            if (!this.visible(range.startContainer)) {
              // if Previous sibling exists in the paragraph, jump to the previous sibling
              if(range.startContainer.parentNode.previousSibling) {
                // When moving left and moving into a hidden element, skip it and go to the previousSibling
                range.setEnd(range.startContainer.parentNode.previousSibling, 0);
                range.moveEnd(ice.dom.CHARACTER_UNIT, ice.dom.getNodeCharacterLength(range.endContainer));
                range.collapse(false);
              }
              // if Previous sibling doesn't exist, get out of the hidden zone by moving to the right
              else {
                range.setEnd(range.startContainer.parentNode.nextSibling, 0);
                range.collapse(false);
              }
            }
          }
          preventDefault = false;
          break;
        case ice.dom.DOM_VK_RIGHT:
          this.pluginsManager.fireCaretPositioned();
          if (browser["type"] === "mozilla") {
            if (!this.visible(range.startContainer)) {
              if(range.startContainer.parentNode.nextSibling) {
                // When moving right and moving into a hidden element, skip it and go to the nextSibling
                range.setStart(range.startContainer.parentNode.nextSibling,0);
                range.collapse(true);
              }
            }
          }
          preventDefault = false;
          break;
        /** END: Handling of caret movements inside hidden .ins/.del elements ***************/
        /************************************************************************************/

        case 32:
          preventDefault = true;
          var range = this.getCurrentRange();
          this._moveRangeToValidTrackingPos(range, range.startContainer);
          this.insert('\u00A0', range);
          break;
        default:
          // Ignore key.
          preventDefault = false;
          break;
      } //end switch

      if (preventDefault === true) {
        ice.dom.preventDefault(e);
        return false;
      }
      return true;
    },

    keyDown: function (e) {
      if (!this.pluginsManager.fireKeyDown(e)) {
        ice.dom.preventDefault(e);
        return false;
      }
      var preventDefault = false;

      if (this._handleSpecialKey(e) === false) {
        if (ice.dom.isBrowser('msie') !== true) {
          this._preventKeyPress = true;
        }

        return false;
      } else if ((e.ctrlKey === true || e.metaKey === true) && (ice.dom.isBrowser('msie') === true || ice.dom.isBrowser('chrome') === true)) {
        // IE does not fire keyPress event if ctrl is also pressed.
        // E.g. CTRL + B (Bold) will not fire keyPress so this.plugins
        // needs to be notified here for IE.
        if (!this.pluginsManager.fireKeyPressed(e)) {
          return false;
        }
      }
      switch (e.keyCode) {
        case 27:
          // ESC
          break;
        default:
          // If not Firefox then check if event is special arrow key etc.
          // Firefox will handle this in keyPress event.
          if (/Firefox/.test(navigator.userAgent) !== true) {
            preventDefault = !(this._handleAncillaryKey(e));
          }
          break;
      }

      if (preventDefault) {
        ice.dom.preventDefault(e);
        return false;
      }
      return true;
    },

    keyPress: function (e) {
      if (this._preventKeyPress === true) {
        this._preventKeyPress = false;
        return;
      }

      if (!this.pluginsManager.fireKeyPress(e)) return false;

      var c = null;
      if (e.which == null) {
        // IE.
        c = String.fromCharCode(e.keyCode);
      } else if (e.which > 0) {
        c = String.fromCharCode(e.which);
      }

      // Inside a br - most likely in a placeholder of a new block - delete before handling.
      var range = this.getCurrentRange();
      var br = ice.dom.parents(range.startContainer, 'br')[0] || null;
      if (br) {
        range.moveToNextEl(br);
        br.parentNode.removeChild(br);
      }

      // Ice will ignore the keyPress event if CMD or CTRL key is also pressed
      if (c !== null && e.ctrlKey !== true && e.metaKey !== true) {
        var key = e.keyCode ? e.keyCode : e.which;
        switch (key) {
          case ice.dom.DOM_VK_DELETE:
            // Handle delete key for Firefox.
            return this._handleAncillaryKey(e);
          case ice.dom.DOM_VK_ENTER:
            return this._handleEnter();
          case 32:
            return this._handleAncillaryKey(e);
          default:
            // If we are in a deletion, move the range to the end/outside.
            this._moveRangeToValidTrackingPos(range, range.startContainer);
            return this.insert();
        }
      }

      return this._handleAncillaryKey(e);
    },

    _handleEnter: function () {
      var range = this.getCurrentRange();
      if (!range.collapsed) this.deleteContents();
      return true;
    },

    _handleSpecialKey: function (e) {
      var keyCode = e.which;
      if (keyCode === null) {
        // IE.
        keyCode = e.keyCode;
      }

      var preventDefault = false;
      switch (keyCode) {
        case 65:
          // Check for CTRL/CMD + A (select all).
          if (e.ctrlKey === true || e.metaKey === true) {
            preventDefault = true;
            var range = this.getCurrentRange();

            if (ice.dom.isBrowser('msie') === true) {
              var selStart = this.env.document.createTextNode('');
              var selEnd = this.env.document.createTextNode('');

              if (this.element.firstChild) {
                ice.dom.insertBefore(this.element.firstChild, selStart);
              } else {
                this.element.appendChild(selStart);
              }

              this.element.appendChild(selEnd);

              range.setStart(selStart, 0);
              range.setEnd(selEnd, 0);
            } else {
              range.setStart(range.getFirstSelectableChild(this.element), 0);
              var lastSelectable = range.getLastSelectableChild(this.element);
              range.setEnd(lastSelectable, lastSelectable.length);
            } //end if

            this.selection.addRange(range);
          } //end if
          break;

        default:
          // Not a special key.
          break;
      } //end switch

      if (preventDefault === true) {
        ice.dom.preventDefault(e);
        return false;
      }

      return true;
    },

    mouseUp: function (e, target) {
      if (!this.pluginsManager.fireClicked(e)) return false;
      this.pluginsManager.fireSelectionChanged(this.getCurrentRange());
    },

    mouseDown: function (e, target) {
      if (!this.pluginsManager.fireMouseDown(e)) return false;
      this.pluginsManager.fireCaretUpdated();
    }
  };

  exports.ice = this.ice || {};
  exports.ice.InlineChangeEditor = InlineChangeEditor;

}).call(this);

(function () {
  var exports = this,
    dom = {};

  dom.DOM_VK_DELETE = 8;
  dom.DOM_VK_LEFT = 37;
  dom.DOM_VK_UP = 38;
  dom.DOM_VK_RIGHT = 39;
  dom.DOM_VK_DOWN = 40;
  dom.DOM_VK_ENTER = 13;
  dom.ELEMENT_NODE = 1;
  dom.ATTRIBUTE_NODE = 2;
  dom.TEXT_NODE = 3;
  dom.CDATA_SECTION_NODE = 4;
  dom.ENTITY_REFERENCE_NODE = 5;
  dom.ENTITY_NODE = 6;
  dom.PROCESSING_INSTRUCTION_NODE = 7;
  dom.COMMENT_NODE = 8;
  dom.DOCUMENT_NODE = 9;
  dom.DOCUMENT_TYPE_NODE = 10;
  dom.DOCUMENT_FRAGMENT_NODE = 11;
  dom.NOTATION_NODE = 12;
  dom.CHARACTER_UNIT = 'character';
  dom.WORD_UNIT = 'word';
  dom.BREAK_ELEMENT = 'br';
  dom.CONTENT_STUB_ELEMENTS = ['img', 'hr', 'iframe', 'param', 'link', 'meta', 'input', 'frame', 'col', 'base', 'area'];
  dom.BLOCK_ELEMENTS = ['p', 'div', 'pre', 'ul', 'ol', 'li', 'table', 'tbody', 'td', 'th', 'fieldset', 'form', 'blockquote', 'dl', 'dt', 'dd', 'dir', 'center', 'address', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
  dom.TEXT_CONTAINER_ELEMENTS = ['p', 'div', 'pre', 'li', 'td', 'th', 'blockquote', 'dt', 'dd', 'center', 'address', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];

  dom.STUB_ELEMENTS = dom.CONTENT_STUB_ELEMENTS.slice();
  dom.STUB_ELEMENTS.push(dom.BREAK_ELEMENT);

  dom.getKeyChar = function (e) {
    return String.fromCharCode(e.which);
  };
  dom.getClass = function (className, startElement, tagName) {
    if (!startElement) {
      startElement = document.body;
    }
    className = '.' + className.split(' ').join('.');
    if (tagName) {
      className = tagName + className;
    }
    return jQuery.makeArray(jQuery(startElement).find(className));
  };
  dom.getId = function (id, startElement) {
    if (!startElement) {
      startElement = document;
    }
    element = startElement.getElementById(id);
    return element;
  };
  dom.getTag = function (tagName, startElement) {
    if (!startElement) {
      startElement = document;
    }
    return jQuery.makeArray(jQuery(startElement).find(tagName));
  };
  dom.getElementWidth = function (element) {
    return element.offsetWidth;
  };
  dom.getElementHeight = function (element) {
    return element.offsetHeight;
  };
  dom.getElementDimensions = function (element) {
    var result = {
      'width': dom.getElementWidth(element),
      'height': dom.getElementHeight(element)
    };
    return result;
  };
  dom.trim = function (string) {
    return jQuery.trim(string);
  };
  dom.empty = function (element) {
    if (element) {
      return jQuery(element).empty();
    }
  };
  dom.remove = function (element) {
    if (element) {
      return jQuery(element).remove();
    }
  };
  dom.prepend = function (parent, elem) {
    jQuery(parent).prepend(elem);
  };
  dom.append = function (parent, elem) {
    jQuery(parent).append(elem);
  };
  dom.insertBefore = function (before, elem) {
    jQuery(before).before(elem);
  };
  dom.insertAfter = function (after, elem) {
    jQuery(after).after(elem);
  };
  dom.getHtml = function (element) {
    return jQuery(element).html();
  };
  dom.setHtml = function (element, content) {
    if (element) {
      jQuery(element).html(content);
    }
  };
  // Remove whitespace/newlines between nested block elements
  // that are supported by ice.
  // For example the following element with innerHTML:
  //   <div><p> para </p> <ul>  <li> hi </li>  </ul></div>
  // Will be converted to the following:
  //   <div><p> para </p><ul><li> hi </li></ul></div>
  dom.removeWhitespace = function(element) {
    jQuery(element).contents().filter(function() {
      // Ice supports UL and OL, so recurse in these blocks to
      // make sure that spaces don't exist between inner LI.
      if (this.nodeType != ice.dom.TEXT_NODE && this.nodeName == 'UL' || this.nodeName == 'OL') {
        dom.removeWhitespace(this);
        return false;
      } else if (this.nodeType != ice.dom.TEXT_NODE) {
        return false;
      } else {
        return !/\S/.test(this.nodeValue);
      }
    }).remove();
  };
  dom.contents = function (el) {
    return jQuery.makeArray(jQuery(el).contents());
  };
  /**
   * Returns the inner contents of `el` as a DocumentFragment.
   */
  dom.extractContent = function (el) {
    var frag = document.createDocumentFragment(),
      child;
    while ((child = el.firstChild)) {
      frag.appendChild(child);
    }
    return frag;
  };

  /**
   * Returns this `node` or the first parent tracking node that matches the given `selector`.
   */
  dom.getNode = function (node, selector) {
    return dom.is(node, selector) ? node : dom.parents(node, selector)[0] || null;
  };

  dom.getParents = function (elements, filter, stopEl) {
    var res = jQuery(elements).parents(filter);
    var ln = res.length;
    var ar = [];
    for (var i = 0; i < ln; i++) {
      if (res[i] === stopEl) {
        break;
      }
      ar.push(res[i]);
    }
    return ar;
  };
  dom.hasBlockChildren = function (parent) {
    var c = parent.childNodes.length;
    for (var i = 0; i < c; i++) {
      if (parent.childNodes[i].nodeType === dom.ELEMENT_NODE) {
        if (dom.isBlockElement(parent.childNodes[i]) === true) {
          return true;
        }
      }
    }
    return false;
  };
  dom.removeTag = function (element, selector) {
    jQuery(element).find(selector).replaceWith(function () {
      return jQuery(this).contents();
    });
    return element;
  };
  dom.stripEnclosingTags = function (content, allowedTags) {
    var c = jQuery(content);
    c.find('*').not(allowedTags).replaceWith(function () {
      var ret = jQuery();
      var $this;
      try{
        $this = jQuery(this);
        ret = $this.contents();
      } catch(e){}

      // Handling jQuery bug (which may be fixed in the official release later)
      // http://bugs.jquery.com/ticket/13401 
      if(ret.length === 0){
        $this.remove();
      }
      return ret;
    });
    return c[0];
  };
  dom.getSiblings = function (element, dir, elementNodesOnly, stopElem) {
    if (elementNodesOnly === true) {
      if (dir === 'prev') {
        return jQuery(element).prevAll();
      } else {
        return jQuery(element).nextAll();
      }
    } else {
      var elems = [];
      if (dir === 'prev') {
        while (element.previousSibling) {
          element = element.previousSibling;
          if (element === stopElem) {
            break;
          }
          elems.push(element);
        }
      } else {
        while (element.nextSibling) {
          element = element.nextSibling;
          if (element === stopElem) {
            break;
          }
          elems.push(element);
        }
      }
      return elems;
    }
  };
  dom.getNodeTextContent = function (node) {
    return jQuery(node).text();
  };
  dom.getNodeStubContent = function (node) {
    return jQuery(node).find(dom.CONTENT_STUB_ELEMENTS.join(', '));
  };
  dom.hasNoTextOrStubContent = function (node) {
    if (dom.getNodeTextContent(node).length > 0) return false;
    if (jQuery(node).find(dom.CONTENT_STUB_ELEMENTS.join(', ')).length > 0) return false;
    return true;
  };
  dom.getNodeCharacterLength = function (node) {
    return dom.getNodeTextContent(node).length + jQuery(node).find(dom.STUB_ELEMENTS.join(', ')).length;
  };
  dom.setNodeTextContent = function (node, txt) {
    return jQuery(node).text(txt);
  };
  dom.getTagName = function (node) {
    return node.tagName && node.tagName.toLowerCase() || null;
  };
  dom.getIframeDocument = function (iframe) {
    var doc = null;
    if (iframe.contentDocument) {
      doc = iframe.contentDocument;
    } else if (iframe.contentWindow) {
      doc = iframe.contentWindow.document;
    } else if (iframe.document) {
      doc = iframe.document;
    }
    return doc;
  };
  dom.isBlockElement = function (element) {
    return dom.BLOCK_ELEMENTS.lastIndexOf(element.nodeName.toLowerCase()) != -1;
  };
  dom.isStubElement = function (element) {
    return dom.STUB_ELEMENTS.lastIndexOf(element.nodeName.toLowerCase()) != -1;
  };
  dom.removeBRFromChild = function (node) {
    if (node && node.hasChildNodes()) {
      for(var z=0; z < node.childNodes.length ; z++) {
        var child = node.childNodes[z];
        if (child && (ice.dom.BREAK_ELEMENT == ice.dom.getTagName(child))) {
          child.parentNode.removeChild(child);
        }
      }
    }
  };
  dom.isChildOf = function (el, parent) {
    try {
      while (el && el.parentNode) {
        if (el.parentNode === parent) {
          return true;
        }
        el = el.parentNode;
      }
    } catch (e) {}
    return false;
  };
  dom.isChildOfTagName = function (el, name) {
    try {
      while (el && el.parentNode) {
        if (el.parentNode && el.parentNode.tagName && el.parentNode.tagName.toLowerCase() === name) {
          return el.parentNode;
        }
        el = el.parentNode;
      }
    } catch (e) {}
    return false;
  };


  dom.isChildOfTagNames = function (el, names) {
    try {
      while (el && el.parentNode) {
        if (el.parentNode && el.parentNode.tagName) {
          tagName = el.parentNode.tagName.toLowerCase();
          for (var i = 0; i < names.length; i++) {
            if (tagName === names[i]) {
              return el.parentNode;
            }
          }
        }
        el = el.parentNode;
      }
    } catch (e) {}
    return null;
  };

  dom.isChildOfClassName = function (el, name) {
    try {
      while (el && el.parentNode) {
        if (jQuery(el.parentNode).hasClass(name)) return el.parentNode;
        el = el.parentNode;
      }
    } catch (e) {}
    return null;
  };
  dom.cloneNode = function (elems, cloneEvents) {
    if (cloneEvents === undefined) {
      cloneEvents = true;
    }
    return jQuery(elems).clone(cloneEvents);
  };

  dom.bind = function (element, event, callback) {
    return jQuery(element).bind(event, callback);
  };

  dom.unbind = function (element, event, callback) {
    return jQuery(element).unbind(event, callback);
  };

  dom.attr = function (elements, key, val) {
    if (val) return jQuery(elements).attr(key, val);
    else return jQuery(elements).attr(key);
  };
  dom.replaceWith = function (node, replacement) {
    return jQuery(node).replaceWith(replacement);
  };
  dom.removeAttr = function (elements, name) {
    jQuery(elements).removeAttr(name);
  };
  dom.getElementsBetween = function (fromElem, toElem) {
    var elements = [];
    if (fromElem === toElem) {
      return elements;
    }
    if (dom.isChildOf(toElem, fromElem) === true) {
      var fElemLen = fromElem.childNodes.length;
      for (var i = 0; i < fElemLen; i++) {
        if (fromElem.childNodes[i] === toElem) {
          break;
        } else if (dom.isChildOf(toElem, fromElem.childNodes[i]) === true) {
          return dom.arrayMerge(elements, dom.getElementsBetween(fromElem.childNodes[i], toElem));
        } else {
          elements.push(fromElem.childNodes[i]);
        }
      }
      return elements;
    }
    var startEl = fromElem.nextSibling;
    while (startEl) {
      if (dom.isChildOf(toElem, startEl) === true) {
        elements = dom.arrayMerge(elements, dom.getElementsBetween(startEl, toElem));
        return elements;
      } else if (startEl === toElem) {
        return elements;
      } else {
        elements.push(startEl);
        startEl = startEl.nextSibling;
      }
    }
    var fromParents = dom.getParents(fromElem);
    var toParents = dom.getParents(toElem);
    var parentElems = dom.arrayDiff(fromParents, toParents, true);
    var pElemLen = parentElems.length;
    for (var j = 0; j < (pElemLen - 1); j++) {
      elements = dom.arrayMerge(elements, dom.getSiblings(parentElems[j], 'next'));
    }
    var lastParent = parentElems[(parentElems.length - 1)];
    elements = dom.arrayMerge(elements, dom.getElementsBetween(lastParent, toElem));
    return elements;
  };
  dom.getCommonAncestor = function (a, b) {
    var node = a;
    while (node) {
      if (dom.isChildOf(b, node) === true) {
        return node;
      }
      node = node.parentNode;
    }
    return null;
  };
  dom.getNextNode = function (node, container) {
    if (node) {
      while (node.parentNode) {
        if (node === container) {
          return null;
        }

        if (node.nextSibling) {
          // if next sibling is an empty text node, look further
          if (node.nextSibling.nodeType === dom.TEXT_NODE && node.nextSibling.length === 0) {
            node = node.nextSibling;
            continue;
          }

          return dom.getFirstChild(node.nextSibling);
        }
        node = node.parentNode;
      }
    }
    return null;
  };
  dom.getNextContentNode = function (node, container) {
    if (node) {
      while (node.parentNode) {
        if (node === container) {
          return null;
        }

        if (node.nextSibling && dom.canContainTextElement(dom.getBlockParent(node))) {
          // if next sibling is an empty text node, look further
          if (node.nextSibling.nodeType === dom.TEXT_NODE && node.nextSibling.length === 0) {
            node = node.nextSibling;
            continue;
          }

          return node.nextSibling;
        } else if (node.nextElementSibling) {
          return node.nextElementSibling;
        }

        node = node.parentNode;
      }
    }
    return null;
  };


  dom.getPrevNode = function (node, container) {
    if (node) {
      while (node.parentNode) {
        if (node === container) {
          return null;
        }

        if (node.previousSibling) {
          // if previous sibling is an empty text node, look further
          if (node.previousSibling.nodeType === dom.TEXT_NODE && node.previousSibling.length === 0) {
            node = node.previousSibling;
            continue;
          }

          return dom.getLastChild(node.previousSibling);
        }
        node = node.parentNode;
      }
    }
    return null;
  };
  dom.getPrevContentNode = function (node, container) {
    if (node) {
      while (node.parentNode) {
        if (node === container) {
          return null;
        }
        if (node.previousSibling && dom.canContainTextElement(dom.getBlockParent(node))) {

          // if previous sibling is an empty text node, look further
          if (node.previousSibling.nodeType === dom.TEXT_NODE && node.previousSibling.length === 0) {
            node = node.previousSibling;

            continue;
          }
          return node.previousSibling;
        } else if (node.previousElementSibling) {
          return node.previousElementSibling;
        }

        node = node.parentNode;
      }
    }
    return null;
  };

  dom.canContainTextElement = function (element) {
    if (element && element.nodeName) {
      return dom.TEXT_CONTAINER_ELEMENTS.lastIndexOf(element.nodeName.toLowerCase()) != -1;
    } else {
      return false;
    }
  };

  dom.getFirstChild = function (node) {
    if (node.firstChild) {
      if (node.firstChild.nodeType === dom.ELEMENT_NODE) {
        return dom.getFirstChild(node.firstChild);
      } else {
        return node.firstChild;
      }
    }
    return node;
  };
  dom.getLastChild = function (node) {
    if (node.lastChild) {
      if (node.lastChild.nodeType === dom.ELEMENT_NODE) {
        return dom.getLastChild(node.lastChild);
      } else {
        return node.lastChild;
      }
    }
    return node;
  };
  dom.removeEmptyNodes = function (parent, callback) {
    var elems = jQuery(parent).find(':empty');
    var i = elems.length;
    while (i > 0) {
      i--;
      if (dom.isStubElement(elems[i]) === false) {
        if (!callback || callback.call(this, elems[i]) !== false) {
          dom.remove(elems[i]);
        }
      }
    }
  };
  dom.create = function (html) {
    return jQuery(html)[0];
  };
  dom.find = function (parent, exp) {
    return jQuery(parent).find(exp);
  };
  dom.children = function (parent, exp) {
    return jQuery(parent).children(exp);
  };
  dom.parent = function (child, exp) {
    return jQuery(child).parent(exp)[0];
  };
  dom.parents = function (child, exp) {
    return jQuery(child).parents(exp);
  };
  dom.is = function (node, exp) {
    return jQuery(node).is(exp);
  };
  dom.extend = function (deep, target, object1, object2) {
    return jQuery.extend.apply(this, arguments);
  };
  dom.walk = function (elem, callback, lvl) {
    if (!elem) {
      return;
    }
    if (!lvl) {
      lvl = 0;
    }
    var retVal = callback.call(this, elem, lvl);
    if (retVal === false) {
      return;
    }
    if (elem.childNodes && elem.childNodes.length > 0) {
      dom.walk(elem.firstChild, callback, (lvl + 1));
    } else if (elem.nextSibling) {
      dom.walk(elem.nextSibling, callback, lvl);
    } else if (elem.parentNode && elem.parentNode.nextSibling) {
      dom.walk(elem.parentNode.nextSibling, callback, (lvl - 1));
    }
  };
  dom.revWalk = function (elem, callback) {
    if (!elem) {
      return;
    }
    var retVal = callback.call(this, elem);
    if (retVal === false) {
      return;
    }
    if (elem.childNodes && elem.childNodes.length > 0) {
      dom.walk(elem.lastChild, callback);
    } else if (elem.previousSibling) {
      dom.walk(elem.previousSibling, callback);
    } else if (elem.parentNode && elem.parentNode.previousSibling) {
      dom.walk(elem.parentNode.previousSibling, callback);
    }
  };
  dom.setStyle = function (element, property, value) {
    if (element) {
      jQuery(element).css(property, value);
    }
  };
  dom.getStyle = function (element, property) {
    return jQuery(element).css(property);
  };
  dom.hasClass = function (element, className) {
    return jQuery(element).hasClass(className);
  };
  dom.addClass = function (element, classNames) {
    jQuery(element).addClass(classNames);
  };
  dom.removeClass = function (element, classNames) {
    jQuery(element).removeClass(classNames);
  };
  dom.preventDefault = function (e) {
    e.preventDefault();
    dom.stopPropagation(e);
  };
  dom.stopPropagation = function (e) {
    e.stopPropagation();
  };
  dom.noInclusionInherits = function (child, parent) {
    if (parent instanceof String || typeof parent === 'string') {
      parent = window[parent];
    }
    if (child instanceof String || typeof child === 'string') {
      child = window[child];
    }
    var above = function () {};
    if (dom.isset(parent) === true) {
      for (value in parent.prototype) {
        if (child.prototype[value]) {
          above.prototype[value] = parent.prototype[value];
          continue;
        }
        child.prototype[value] = parent.prototype[value];
      }
    }
    if (child.prototype) {
      above.prototype.constructor = parent;
      child.prototype['super'] = new above();
    }
  };

  dom.each = function (val, callback) {
    jQuery.each(val, function (i, el) {
      callback.call(this, i, el);
    });
  };

  dom.foreach = function (value, cb) {
    if (value instanceof Array || value instanceof NodeList || typeof value.length != 'undefined' && typeof value.item != 'undefined') {
      var len = value.length;
      for (var i = 0; i < len; i++) {
        var res = cb.call(this, i, value[i]);
        if (res === false) {
          break;
        }
      }
    } else {
      for (var id in value) {
        if (value.hasOwnProperty(id) === true) {
          var res = cb.call(this, id);
          if (res === false) {
            break;
          }
        }
      }
    }
  };
  dom.isBlank = function (value) {
    if (!value || /^\s*$/.test(value)) {
      return true;
    }
    return false;
  };
  dom.isFn = function (f) {
    if (typeof f === 'function') {
      return true;
    }
    return false;
  };
  dom.isObj = function (v) {
    if (v !== null && typeof v === 'object') {
      return true;
    }
    return false;
  };
  dom.isset = function (v) {
    if (typeof v !== 'undefined' && v !== null) {
      return true;
    }
    return false;
  };
  dom.isArray = function (v) {
    return jQuery.isArray(v);
  };
  dom.isNumeric = function (str) {
    var result = str.match(/^\d+$/);
    if (result !== null) {
      return true;
    }
    return false;
  };
  dom.getUniqueId = function () {
    var timestamp = (new Date()).getTime();
    var random = Math.ceil(Math.random() * 1000000);
    var id = timestamp + '' + random;
    return id.substr(5, 18).replace(/,/, '');
  };
  dom.inArray = function (needle, haystack) {
    var hln = haystack.length;
    for (var i = 0; i < hln; i++) {
      if (needle === haystack[i]) {
        return true;
      }
    }
    return false;
  };
  dom.arrayDiff = function (array1, array2, firstOnly) {
    var al = array1.length;
    var res = [];
    for (var i = 0; i < al; i++) {
      if (dom.inArray(array1[i], array2) === false) {
        res.push(array1[i]);
      }
    }
    if (firstOnly !== true) {
      al = array2.length;
      for (var i = 0; i < al; i++) {
        if (dom.inArray(array2[i], array1) === false) {
          res.push(array2[i]);
        }
      }
    }
    return res;
  };
  dom.arrayMerge = function (array1, array2) {
    var c = array2.length;
    for (var i = 0; i < c; i++) {
      array1.push(array2[i]);
    }
    return array1;
  };
  /**
   * Removes allowedTags from the given content html string. If allowedTags is a string, then it
   * is expected to be a selector; otherwise, it is expected to be array of string tag names.
   */
  dom.stripTags = function (content, allowedTags) {
    if (typeof allowedTags === "string") {
      var c = jQuery('<div>' + content + '</div>');
      c.find('*').not(allowedTags).remove();
      return c.html();
    } else {
      var match;
      var re = new RegExp(/<\/?(\w+)((\s+\w+(\s*=\s*(?:".*?"|'.*?'|[^'">\s]+))?)+\s*|\s*)\/?>/gim);
      var resCont = content;
      while ((match = re.exec(content)) != null) {
        if (dom.isset(allowedTags) === false || dom.inArray(match[1], allowedTags) !== true) {
          resCont = resCont.replace(match[0], '');
        }
      }
      return resCont;
    }
  };
  dom.browser = function () {
    var result = {};
    result.version = jQuery.browser.version;
    if (jQuery.browser.mozilla === true) {
      result.type = 'mozilla';
    } else if (jQuery.browser.msie === true) {
      result.type = 'msie';
    } else if (jQuery.browser.opera === true) {
      result.type = 'opera';
    } else if (jQuery.browser.webkit === true) {
      result.type = 'webkit';
    }
    return result;
  };
  dom.getBrowserType = function () {
    if (this._browserType === null) {
      var tests = ['msie', 'firefox', 'chrome', 'safari'];
      var tln = tests.length;
      for (var i = 0; i < tln; i++) {
        var r = new RegExp(tests[i], 'i');
        if (r.test(navigator.userAgent) === true) {
          this._browserType = tests[i];
          return this._browserType;
        }
      }

      this._browserType = 'other';
    }
    return this._browserType;
  };
  dom.getWebkitType = function(){
	if(dom.browser().type !== "webkit") {
		console.log("Not a webkit!");
		return false;
	}
    var isSafari = Object.prototype.toString.call(window.HTMLElement).indexOf('Constructor') > 0;
	if(isSafari) return "safari";
	return "chrome";
  };
  dom.isBrowser = function (browser) {
    return (dom.browser().type === browser);
  };

  dom.getBlockParent = function (node, container) {
    if (dom.isBlockElement(node) === true) {
      return node;
    }
    if (node) {
      while (node.parentNode) {
        node = node.parentNode;
        if (node === container) {
          return null;
        }

        if (dom.isBlockElement(node) === true) {
          return node;
        }
      }
    }
    return null;
  };
  dom.findNodeParent = function (node, selector, container) {
    if (node) {
      while (node.parentNode) {
        if (node === container) {
          return null;
        }

        if (dom.is(node, selector) === true) {
          return node;
        }
        node = node.parentNode;
      }
    }
    return null;
  };
  dom.onBlockBoundary = function (leftContainer, rightContainer, blockEls) {
    if (!leftContainer || !rightContainer) return false
    var bleft = dom.isChildOfTagNames(leftContainer, blockEls) || dom.is(leftContainer, blockEls.join(', ')) && leftContainer || null;
    var bright = dom.isChildOfTagNames(rightContainer, blockEls) || dom.is(rightContainer, blockEls.join(', ')) && rightContainer || null;
    return (bleft !== bright);
  };

  dom.isOnBlockBoundary = function (leftContainer, rightContainer, container) {
    if (!leftContainer || !rightContainer) return false
    var bleft = dom.getBlockParent(leftContainer, container) || dom.isBlockElement(leftContainer, container) && leftContainer || null;
    var bright = dom.getBlockParent(rightContainer, container) || dom.isBlockElement(rightContainer, container) && rightContainer || null;
    return (bleft !== bright);
  };

  dom.mergeContainers = function (node, mergeToNode) {
    if (!node || !mergeToNode) return false;

    if (node.nodeType === dom.TEXT_NODE || dom.isStubElement(node)) {
      // Move only this node.
      mergeToNode.appendChild(node);
    } else if (node.nodeType === dom.ELEMENT_NODE) {
      // Move all the child nodes to the new parent.
      while (node.firstChild) {
        mergeToNode.appendChild(node.firstChild);
      }

      dom.remove(node);
    }
    return true;
  };

  dom.mergeBlockWithSibling = function (range, block, next) {
    var siblingBlock = next ? jQuery(block).next().get(0) : jQuery(block).prev().get(0); // block['nextSibling'] : block['previousSibling'];
    if (next) dom.mergeContainers(siblingBlock, block);
    else dom.mergeContainers(block, siblingBlock);
    range.collapse(true);
    return true;
  };

  dom.date = function (format, timestamp, tsIso8601) {
    if (timestamp === null && tsIso8601) {
      timestamp = dom.tsIso8601ToTimestamp(tsIso8601);
      if (!timestamp) {
        return;
      }
    }
    var date = new Date(timestamp);
    var formats = format.split('');
    var fc = formats.length;
    var dateStr = '';
    for (var i = 0; i < fc; i++) {
      var r = '';
      var f = formats[i];
      switch (f) {
        case 'D':
        case 'l':
          var names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
          r = names[date.getDay()];
          if (f === 'D') {
            r = r.substring(0, 3);
          }
          break;
        case 'F':
        case 'm':
          r = date.getMonth() + 1;
          if (r < 10) r = '0' + r;
          break;
        case 'M':
          months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
          r = months[date.getMonth()];
          if (f === 'M') {
            r = r.substring(0, 3);
          }
          break;
        case 'd':
          r = date.getDate();
          break;
        case 'S':
          r = dom.getOrdinalSuffix(date.getDate());
          break;
        case 'Y':
          r = date.getFullYear();
          break;
        case 'y':
          r = date.getFullYear();
          r = r.toString().substring(2);
          break;
        case 'H':
          r = date.getHours();
          break;
        case 'h':
          r = date.getHours();
          if (r === 0) {
            r = 12;
          } else if (r > 12) {
            r -= 12;
          }
          break;
        case 'i':
          r = dom.addNumberPadding(date.getMinutes());
          break;
        case 'a':
          r = 'am';
          if (date.getHours() >= 12) {
            r = 'pm';
          }
          break;
        default:
          r = f;
          break;
      }
      dateStr += r;
    }
    return dateStr;
  };
  dom.getOrdinalSuffix = function (number) {
    var suffix = '';
    var tmp = (number % 100);
    if (tmp >= 4 && tmp <= 20) {
      suffix = 'th';
    } else {
      switch (number % 10) {
        case 1:
          suffix = 'st';
          break;
        case 2:
          suffix = 'nd';
          break;
        case 3:
          suffix = 'rd';
          break;
        default:
          suffix = 'th';
          break;
      }
    }
    return suffix;
  };
  dom.addNumberPadding = function (number) {
    if (number < 10) {
      number = '0' + number;
    }
    return number;
  };
  dom.tsIso8601ToTimestamp = function (tsIso8601) {
    var regexp = /(\d\d\d\d)(?:-?(\d\d)(?:-?(\d\d)(?:[T ](\d\d)(?::?(\d\d)(?::?(\d\d)(?:\.(\d+))?)?)?(?:Z|(?:([-+])(\d\d)(?::?(\d\d))?)?)?)?)?)?/;
    var d = tsIso8601.match(new RegExp(regexp));
    if (d) {
      var date = new Date();
      date.setDate(d[3]);
      date.setFullYear(d[1]);
      date.setMonth(d[2] - 1);
      date.setHours(d[4]);
      date.setMinutes(d[5]);
      date.setSeconds(d[6]);
      var offset = (d[9] * 60);
      if (d[8] === '+') {
        offset *= -1;
      }
      offset -= date.getTimezoneOffset();
      var timestamp = (date.getTime() + (offset * 60 * 1000));
      return timestamp;
    }
    return null;
  };

  exports.dom = dom;

}).call(this.ice);

(function() {

  var exports = this, Bookmark;

  Bookmark = function(env, range, keepOldBookmarks) {

    this.env = env;
    this.element = env.element;
    this.selection = this.env.selection;

    // Remove all bookmarks?
    if (!keepOldBookmarks) {
      this.removeBookmarks(this.element);
    }

    var currRange = range || this.selection.getRangeAt(0);
    range = currRange.cloneRange();
    var startContainer = range.startContainer;
    var endContainer = range.endContainer;
    var startOffset  = range.startOffset;
    var endOffset = range.endOffset;
    var tmp;

    // Collapse to the end of range.
    range.collapse(false);

    var endBookmark  = this.env.document.createElement('span');
    endBookmark.style.display = 'none';
    ice.dom.setHtml(endBookmark, '&nbsp;');
    ice.dom.addClass(endBookmark, 'iceBookmark iceBookmark_end');
    endBookmark.setAttribute('iceBookmark', 'end');
    range.insertNode(endBookmark);
    if(!ice.dom.isChildOf(endBookmark, this.element)) {
      this.element.appendChild(endBookmark);
    }

    // Move the range to where it was before.
    range.setStart(startContainer, startOffset);
    range.collapse(true);

    // Create the start bookmark.
    var startBookmark = this.env.document.createElement('span');
    startBookmark.style.display = 'none';
    ice.dom.addClass(startBookmark, 'iceBookmark iceBookmark_start');
    ice.dom.setHtml(startBookmark, '&nbsp;');
    startBookmark.setAttribute('iceBookmark', 'start');
    try {
      range.insertNode(startBookmark);

      // Make sure start and end are in correct position.
      if (startBookmark.previousSibling === endBookmark) {
        // Reverse..
        tmp  = startBookmark;
        startBookmark = endBookmark;
        endBookmark = tmp;
      }
    } catch (e) {
      // NS_ERROR_UNEXPECTED: I believe this is a Firefox bug.
      // It seems like if the range is collapsed and the text node is empty
      // (i.e. length = 0) then Firefox tries to split the node for no reason and fails...
      ice.dom.insertBefore(endBookmark, startBookmark);
    }

    if (ice.dom.isChildOf(startBookmark, this.element) === false) {
      if (this.element.firstChild) {
        ice.dom.insertBefore(this.element.firstChild, startBookmark);
      } else {
        // Should not happen...
        this.element.appendChild(startBookmark);
      }
    }

    if (!endBookmark.previousSibling) {
      tmp = this.env.document.createTextNode('');
      ice.dom.insertBefore(endBookmark, tmp);
    }

    // The original range object must be changed.
    if (!startBookmark.nextSibling) {
      tmp = this.env.document.createTextNode('');
      ice.dom.insertAfter(startBookmark, tmp);
    }

    currRange.setStart(startBookmark.nextSibling, 0);
    currRange.setEnd(endBookmark.previousSibling, (endBookmark.previousSibling.length || 0));

    this.start = startBookmark;
    this.end = endBookmark;
  };

  Bookmark.prototype = {

    selectBookmark: function() {
      var range = this.selection.getRangeAt(0);
      var startPos = null;
      var endPos = null;
      var startOffset = 0;
      var endOffset = null;
      if (this.start.nextSibling === this.end || ice.dom.getElementsBetween(this.start, this.end).length === 0) {
        // Bookmark is collapsed.
        if (this.end.nextSibling) {
          startPos = ice.dom.getFirstChild(this.end.nextSibling);
        } else if (this.start.previousSibling) {
          startPos = ice.dom.getFirstChild(this.start.previousSibling);
          if (startPos.nodeType === ice.dom.TEXT_NODE) {
            startOffset = startPos.length;
          }
        } else {
          // Create a text node in parent.
          this.end.parentNode.appendChild(this.env.document.createTextNode(''));
          startPos = ice.dom.getFirstChild(this.end.nextSibling);
        }
      } else {
        if (this.start.nextSibling) {
          startPos = ice.dom.getFirstChild(this.start.nextSibling);
        } else {
          if (!this.start.previousSibling) {
            var tmp = this.env.document.createTextNode('');
            ice.dom.insertBefore(this.start, tmp);
          }

          startPos = ice.dom.getLastChild(this.start.previousSibling);
          startOffset = startPos.length;
        }

        if (this.end.previousSibling) {
          endPos = ice.dom.getLastChild(this.end.previousSibling);
        } else {
          endPos = ice.dom.getFirstChild(this.end.nextSibling || this.end);
          endOffset = 0;
        }
      }

      ice.dom.remove([this.start, this.end]);

      if (endPos === null) {
        range.setEnd(startPos, startOffset);
        range.collapse(false);
      } else {
        range.setStart(startPos, startOffset);
        if (endOffset === null) {
          endOffset = (endPos.length || 0);
        }
        range.setEnd(endPos, endOffset);
      }

      try {
        this.selection.addRange(range);
      } catch (e) {
        // IE may throw exception for hidden elements..
      }
    },

    getBookmark: function(parent, type) {
      var elem = ice.dom.getClass('iceBookmark_' + type, parent)[0];
      return elem;
    },

    removeBookmarks: function(elem) {
      ice.dom.remove(ice.dom.getClass('iceBookmark', elem, 'span'));
    }
  };

  exports.Bookmark = Bookmark;

}).call(this.ice);
(function () {

  var exports = this,
    Selection;

  Selection = function (env) {
    this._selection = null;
    this.env = env;

    this._initializeRangeLibrary();
    this._getSelection();
  };

  Selection.prototype = {

    /**
     * Returns the selection object for the current browser.
     */
    _getSelection: function () {
      if (this._selection) {
      this._selection.refresh();
    }
      else if (this.env.frame) {
      this._selection = rangy.getIframeSelection(this.env.frame);
    }
      else {
      this._selection = rangy.getSelection();
    }
      return this._selection;
    },

    /**
     * Creates a range object.
     */
    createRange: function () {
      return rangy.createRange(this.env.document);
    },

    /**
     * Returns the range object at the specified position. The current range object
     * is at position 0. Note - currently only setting single range in `addRange` so
     * position 0 will be the only allocation filled.
     */
    getRangeAt: function (pos) {
      this._selection.refresh();
      try {
        return this._selection.getRangeAt(pos);
      } catch (e) {
        this._selection = null;
        return this._getSelection().getRangeAt(0);
      }
    },

    /**
     * Adds the specified range to the current selection. Note - only supporting setting
     * a single range, so the previous range gets evicted.
     */
    addRange: function (range) {
      this._selection || (this._selection = this._getSelection());
      this._selection.setSingleRange(range);
      this._selection.ranges = [range];
      return;
    },

    /**
     * Initialize and extend the `rangy` library with some custom functionality.
     */
    _initializeRangeLibrary: function () {
      var self = this;

      rangy.init();
      rangy.config.checkSelectionRanges = false;

      var move = function (range, unitType, units, isStart) {
        if (units === 0) {
      return;
        }

        switch (unitType) {
          case ice.dom.CHARACTER_UNIT:
            if (units > 0) {
              range.moveCharRight(isStart, units);
            } else {
              range.moveCharLeft(isStart, units * -1);
            }
            break;

          case ice.dom.WORD_UNIT:
          default:
            // Removed. TODO: possibly refactor or re-implement.
            break;
        }
      };

      /**
       * Moves the start of the range using the specified `unitType`, by the specified
       * number of `units`. Defaults to `CHARACTER_UNIT` and units of 1.
       */
      rangy.rangePrototype.moveStart = function (unitType, units) {
        move(this, unitType, units, true);
      };

      /**
       * Moves the end of the range using the specified `unitType`, by the specified
       * number of `units`.
       */
      rangy.rangePrototype.moveEnd = function (unitType, units) {
        move(this, unitType, units, false);
      };

      /**
       * Depending on the given `start` boolean, sets the start or end containers
       * to the given `container` with `offset` units.
       */
      rangy.rangePrototype.setRange = function (start, container, offset) {
        if (start) {
          this.setStart(container, offset);
        } else {
          this.setEnd(container, offset);
        }
      };

      /**
       * Depending on the given `moveStart` boolean, moves the start or end containers
       * to the left by the given number of character `units`. Use the following
       * example as a demonstration for where the range will fall as it moves in and
       * out of tag boundaries (where "|" is the marked range):
       *
       * test <em>it</em> o|ut
       * test <em>it</em> |out
       * test <em>it</em>| out
       * test <em>i|t</em> out
       * test <em>|it</em> out
       * test| <em>it</em> out
       * tes|t <em>it</em> out
       *
       * A range could be mapped in one of two ways:
       *
       * (1) If a startContainer is a Node of type Text, Comment, or CDATASection, then startOffset
       * is the number of characters from the start of startNode. For example, the following
       * are the range properties for `<p>te|st</p>` (where "|" is the collapsed range):
       *
       * startContainer: <TEXT>test<TEXT>
       * startOffset: 2
       * endContainer: <TEXT>test<TEXT>
       * endOffset: 2
       *
       * (2) For other Node types, startOffset is the number of child nodes between the start of
       * the startNode. Take the following html fragment:
       *
       * `<p>some <span>test</span> text</p>`
       *
       * If we were working with the following range properties:
       *
       * startContainer: <p>
       * startOffset: 2
       * endContainer: <p>
       * endOffset: 2
       *
       * Since <p> is an Element node, the offsets are based on the offset in child nodes of <p> and
       * the range is selecting the second child - the <span> tag.
       *
       * <p><TEXT>some </TEXT><SPAN>test</SPAN><TEXT> text</TEXT></p>
       */
      rangy.rangePrototype.moveCharLeft = function (moveStart, units) {
        var container, offset;

        if (moveStart) {
          container = this.startContainer;
          offset = this.startOffset;
        } else {
          container = this.endContainer;
          offset = this.endOffset;
        }

        // Handle the case where the range conforms to (2) (noted in the comment above).
        if (container.nodeType === ice.dom.ELEMENT_NODE) {
          if (container.hasChildNodes() && offset > 0) {
            var lastChild = container.childNodes[offset - 1],
              nextContainer = this.getLastSelectableChild(lastChild);

            container = (nextContainer) ? nextContainer : this.getPreviousTextNode(lastChild);

            if (! container) {
              return;
            }

            offset = container.data.length - units;
          } else {
            offset = units * -1;
          }
        } else {
          offset -= units;
        }

        if (offset < 0) {
          // We need to move to a previous selectable container.
          while (offset < 0) {
            container = this.getPreviousTextNode(container);

            // We are at the beginning/out of the editable - break.
            if (!container) {
              return;
            }

            if (container.nodeType === ice.dom.ELEMENT_NODE) {
              continue;
            }

            offset += container.data.length;
          }
        }

        this.setRange(moveStart, container, offset);
      };

      /**
       * Depending on the given `moveStart` boolean, moves the start or end containers
       * to the right by the given number of character `units`. Use the following
       * example as a demonstration for where the range will fall as it moves in and
       * out of tag boundaries (where "|" is the marked range):
       *
       * tes|t <em>it</em> out
       * test| <em>it</em> out
       * test |<em>it</em> out
       * test <em>i|t</em> out
       * test <em>it|</em> out
       * test <em>it</em> |out
       *
       * A range could be mapped in one of two ways:
       *
       * (1) If a startContainer is a Node of type Text, Comment, or CDATASection, then startOffset
       * is the number of characters from the start of startNode. For example, the following
       * are the range properties for `<p>te|st</p>` (where "|" is the collapsed range):
       *
       * startContainer: <TEXT>test<TEXT>
       * startOffset: 2
       * endContainer: <TEXT>test<TEXT>
       * endOffset: 2
       *
       * (2) For other Node types, startOffset is the number of child nodes between the start of
       * the startNode. Take the following html fragment:
       *
       * `<p>some <span>test</span> text</p>`
       *
       * If we were working with the following range properties:
       *
       * startContainer: <p>
       * startOffset: 2
       * endContainer: <p>
       * endOffset: 2
       *
       * Since <p> is an Element node, the offsets are based on the offset in child nodes of <p> and
       * the range is selecting the second child - the <span> tag.
       *
       * <p><TEXT>some </TEXT><SPAN>test</SPAN><TEXT> text</TEXT></p>
       */
      rangy.rangePrototype.moveCharRight = function (moveStart, units) {
        var container, offset;

        if (moveStart) {
          container = this.startContainer;
          offset = this.startOffset;
        } else {
          container = this.endContainer;
          offset = this.endOffset;
        }

        if (container.nodeType === ice.dom.ELEMENT_NODE) {
          container = container.childNodes[offset];
          if (container && container.nodeType !== ice.dom.TEXT_NODE) {
            container = this.getNextTextNode(container);
          }

          offset = units;
        } else {
          offset += units;
        }

        var diff = (offset - container.data.length);
        if (diff > 0) {
          var skippedBlockElem = [];
          // We need to move to the next selectable container.
          while (diff > 0) {
            container = this.getNextContainer(container, skippedBlockElem);

            if (container.nodeType === ice.dom.ELEMENT_NODE) {
              continue;
            }

            if (container.data.length >= diff) {
              // We found a container with enough content to select.
              break;
            } else if (container.data.length > 0) {
              // Container does not have enough content,
              // find the next one.
              diff -= container.data.length;
            }
          }

          offset = diff;
        }

        this.setRange(moveStart, container, offset);
      };

      /**
       * Returns the deepest next container that the range can be extended to.
       * For example, if the next container is an element that contains text nodes,
       * the the container's firstChild is returned.
       */
      rangy.rangePrototype.getNextContainer = function (container, skippedBlockElem) {
        if (!container) {
          return null;
        }

        while (container.nextSibling) {
          container = container.nextSibling;
          if (container.nodeType !== ice.dom.TEXT_NODE) {
            var child = this.getFirstSelectableChild(container);
            if (child !== null) {
              return child;
            }
          } else if (this.isSelectable(container) === true) {
            return container;
          }
        }

        // Look at parents next sibling.
        while (container && !container.nextSibling) {
          container = container.parentNode;
        }

        if (!container) {
          return null;
        }

        container = container.nextSibling;
        if (this.isSelectable(container) === true) {
          return container;
        } else if (skippedBlockElem && ice.dom.isBlockElement(container) === true) {
          skippedBlockElem.push(container);
        }

        var selChild = this.getFirstSelectableChild(container);
        if (selChild !== null) {
          return selChild;
        }

        return this.getNextContainer(container, skippedBlockElem);
      };

      /**
       * Returns the deepest previous container that the range can be extended to.
       * For example, if the previous container is an element that contains text nodes,
       * then the container's lastChild is returned.
       */
      rangy.rangePrototype.getPreviousContainer = function (container, skippedBlockElem) {
        if (!container) {
          return null;
        }

        while (container.previousSibling) {
          container = container.previousSibling;
          if (container.nodeType !== ice.dom.TEXT_NODE) {
            if (ice.dom.isStubElement(container) === true) {
              return container;
            } else {
              var child = this.getLastSelectableChild(container);
              if (child !== null) {
                return child;
              }
            }
          } else if (this.isSelectable(container) === true) {
            return container;
          }
        }

        // Look at parents next sibling.
        while (container && !container.previousSibling) {
          container = container.parentNode;
        }

        if (!container) {
          return null;
        }

        container = container.previousSibling;
        if (this.isSelectable(container) === true) {
          return container;
        } else if (skippedBlockElem && ice.dom.isBlockElement(container) === true) {
          skippedBlockElem.push(container);
        }

        var selChild = this.getLastSelectableChild(container);
        if (selChild !== null) {
          return selChild;
        }
        return this.getPreviousContainer(container, skippedBlockElem);
      };

      rangy.rangePrototype.getNextTextNode = function (container) {
        if (container && container.nodeType === ice.dom.ELEMENT_NODE) {
          if (container.childNodes.length !== 0) {
            return this.getFirstSelectableChild(container);
          }
        }

        container = this.getNextContainer(container);
        if (container && container.nodeType === ice.dom.TEXT_NODE) {
          return container;
        }

        return this.getNextTextNode(container);
      };

      rangy.rangePrototype.getPreviousTextNode = function (container, skippedBlockEl) {
        container = this.getPreviousContainer(container, skippedBlockEl);
        if (container && container.nodeType === ice.dom.TEXT_NODE) {
          return container;
        }

        return this.getPreviousTextNode(container, skippedBlockEl);
      };

      rangy.rangePrototype.getFirstSelectableChild = function (element) {
        if (element) {
          if (element.nodeType !== ice.dom.TEXT_NODE) {
            var child = element.firstChild;
            while (child) {
              if (this.isSelectable(child) === true) {
                return child;
              } else if (child.firstChild) {
                // This node does have child nodes.
                var res = this.getFirstSelectableChild(child);
                if (res !== null) {
                  return res;
                } else {
                  child = child.nextSibling;
                }
              } else {
                child = child.nextSibling;
              }
            }
          } else {
            // Given element is a text node so return it.
            return element;
          }
        }
        return null;
      };

      rangy.rangePrototype.getLastSelectableChild = function (element) {
        if (element) {
          if (element.nodeType !== ice.dom.TEXT_NODE) {
            var child = element.lastChild;
            while (child) {
              if (this.isSelectable(child) === true) {
                return child;
              } else if (child.lastChild) {
                // This node does have child nodes.
                var res = this.getLastSelectableChild(child);
                if (res !== null) {
                  return res;
                } else {
                  child = child.previousSibling;
                }
              } else {
                child = child.previousSibling;
              }
            }
          } else {
            // Given element is a text node so return it.
            return element;
          }
        }
        return null;
      };

      rangy.rangePrototype.isSelectable = function (container) {
        if (container && container.nodeType === ice.dom.TEXT_NODE && container.data.length !== 0) {
          return true;
        }
        return false;
      };

      rangy.rangePrototype.getHTMLContents = function (clonedSelection) {
        if (!clonedSelection) {
          clonedSelection = this.cloneContents();
        }
        var div = self.env.document.createElement('div');
        div.appendChild(clonedSelection.cloneNode(true));
        return div.innerHTML;
      };

      rangy.rangePrototype.getHTMLContentsObj = function () {
        return this.cloneContents();
      };
    }
  };

  exports.Selection = Selection;

}).call(this.ice);

(function() {

var exports = this;

var IcePlugin = function(ice_instance) {
  this._ice = ice_instance;
};

IcePlugin.prototype = {

  start: function() {},
  clicked: function(e) {
    return true;
  },
  mouseDown: function(e) {
    return true;
  },
  keyDown: function(e) {
    return true;
  },
  keyPress: function(e) {
    return true;
  },
  selectionChanged: function(range) {},
  setEnabled: function(enabled) {},
  setDisabled: function(enabled) {},
  caretUpdated: function() {},
  nodeInserted: function(node, range) {},
  nodeCreated: function(node, options) {},
  caretPositioned: function() {},
  remove: function() {
    this._ice.removeKeyPressListener(this);
  },
  setSettings: function(settings) {}
};

exports.IcePlugin = IcePlugin;

}).call(this.ice);

(function() {

var exports = this;

var IcePluginManager = function(ice_instance) {

  this.plugins = {},
  this.pluginConstructors = {},
  this.keyPressListeners = {},
  this.activePlugin = null,
  this.pluginSets = {},
  this.activePluginSet = null,

  this._ice = ice_instance;
};

IcePluginManager.prototype = {

  getPluginNames: function() {
    var plugins = [];
    for (var name in this.plugins) {
      plugins.push(name);
    }
    return plugins;
  },

  addPluginObject: function(pluginName, pluginObj) {
    this.plugins[pluginName] = pluginObj;
  },

  addPlugin: function(name, pluginConstructor) {
    if (typeof pluginConstructor !== 'function') {
      throw Error('IcePluginException: plugin must be a constructor function');
    }

    if (ice.dom.isset(this.pluginConstructors[name]) === false) {
      this.pluginConstructors[name] = pluginConstructor;
    }
  },

  loadPlugins: function(plugins, callback) {
    if (plugins.length === 0) {
      callback.call(this);
    } else {
      var plugin = plugins.shift();
      if (typeof plugin === 'object') {
        plugin = plugin.name;
      }

      if (ice.dom.isset(ice._plugin[plugin]) === true) {
        this.addPlugin(plugin, ice._plugin[plugin]);
        this.loadPlugins(plugins, callback);
      } else {
        throw new Error('plugin was not included in the page: ' + plugin);
      }
    }
  },

  _enableSet: function(name) {
    this.activePluginSet = name;
    var pSetLen = this.pluginSets[name].length;
    for (var i = 0; i < pSetLen; i++) {
      var plugin   = this.pluginSets[name][i];
      var pluginName = '';
      if (typeof plugin === 'object') {
        pluginName = plugin.name;
      } else {
        pluginName = plugin;
      }

      var pluginConstructor = this.pluginConstructors[pluginName];
      if (pluginConstructor) {
        var pluginObj = new pluginConstructor(this._ice);
        this.plugins[pluginName] = pluginObj;

        if (ice.dom.isset(plugin.settings) === true) {
          pluginObj.setSettings(plugin.settings);
        }

        pluginObj.start();
      }
    }
  },

  setActivePlugin: function(name) {
    this.activePlugin = name;
  },

  getActivePlugin: function() {
    return this.activePlugin;
  },

  _getPluginName: function(pluginConstructor) {
    var fn = pluginConstructor.toString();
    var start = 'function '.length;
    var name = fn.substr(start, (fn.indexOf('(') - start));
    return name;
  },

  /**
   * Removes specified plugin.
   */
  removePlugin: function(plugin) {
    if (this.plugins[plugin]) {
      // Call the remove fn of the plugin incase it needs to do cleanup.
      this.plugins[plugin].remove();
    }
  },

  /**
   * Returns the plugin object for specified plugin name.
   */
  getPlugin: function(name) {
    return this.plugins[name];

  },

  /**
   * Add a new set of plugins.
   */
  usePlugins: function(name, plugins, callback) {
    var self = this;
    if (ice.dom.isset(plugins) === true) {
      this.pluginSets[name] = plugins;
    } else {
      this.pluginSets[name] = [];
    }
    var clone = this.pluginSets[name].concat([]);
    this.loadPlugins(clone, function() {
      self._enableSet(name);
      if(callback) callback.call(this);
    });
  },

  disablePlugin: function(name) {
    this.plugins[name].disable();
  },

  isPluginElement: function(element) {
    for (var i in this.plugins) {
      if (this.plugins[i].isPluginElement) {
        if (this.plugins[i].isPluginElement(element) === true) {
          return true;
        }
      }
    }
    return false;
  },

  fireKeyPressed: function(e) {
    if (this._fireKeyPressFns(e, 'all_keys') === false) {
      return false;
    }

    var eKeys = [];
    if (e.ctrlKey === true || e.metaKey === true) {
      eKeys.push('ctrl');
    }

    if (e.shiftKey === true) {
      eKeys.push('shift');
    }

    if (e.altKey === true) {
      eKeys.push('alt');
    }

    switch (e.keyCode) {
      case 13:
        eKeys.push('enter');
      break;

      case ice.dom.DOM_VK_LEFT:
        eKeys.push('left');
      break;

      case ice.dom.DOM_VK_RIGHT:
        eKeys.push('right');
      break;

      case ice.dom.DOM_VK_UP:
        eKeys.push('up');
      break;

      case ice.dom.DOM_VK_DOWN:
        eKeys.push('down');
      break;

      case 9:
        eKeys.push('tab');
      break;

      case ice.dom.DOM_VK_DELETE:
        eKeys.push('delete');
      break;

      default:
        var code;
        if (e.keyCode) {
          code = e.keyCode;
        } else if (e.which) {
          code = e.which;
        }

        // Other characters (a-z0-9..).
        if (code) {
          eKeys.push(String.fromCharCode(code).toLowerCase());
        }
      break;
    }//end switch

    var eKeysStr = eKeys.sort().join('+');

    return this._fireKeyPressFns(e, eKeysStr);

  },

  _fireKeyPressFns: function(e, eKeysStr) {
    if (this.keyPressListeners[eKeysStr]) {
      var ln = this.keyPressListeners[eKeysStr].length;
      for (var i = 0; i < ln; i++) {
        var listener = this.keyPressListeners[eKeysStr][i];
        var eventFn  = listener.fn;
        var plugin   = listener.plugin;
        var data   = listener.data;

        if (eventFn) {
          if (ice.dom.isFn(eventFn) === true) {
            if (eventFn.call(plugin, e, data) === true) {
              ice.dom.preventDefault(e);
              return false;
            }
          } else if (plugin[eventFn] && plugin[eventFn].call(plugin, e, data) === true) {
            ice.dom.preventDefault(e);
            return false;
          }
        }
      }
    }

    return true;
  },

  fireSelectionChanged: function(range) {
    for (var i in this.plugins) {
      this.plugins[i].selectionChanged(range);
    }
  },

  fireNodeInserted: function(node, range) {
    for (var i in this.plugins) {
      if (this.plugins[i].nodeInserted(node, range) === false) {
        return false;
      }
    }
  },

  fireNodeCreated: function(node, option) {
    for (var i in this.plugins) {
      if (this.plugins[i].nodeCreated(node, option) === false) {
        return false;
      }
    }
  },

  fireCaretPositioned: function() {
    for (var i in this.plugins) {
      this.plugins[i].caretPositioned()
    }
  },

  fireClicked: function(e) {
    var val = true;
    for (var i in this.plugins) {
      if (this.plugins[i].clicked(e) === false) {
        val = false;
      }
    }
    return val;
  },

  fireMouseDown: function(e) {
    var val = true;
    for (var i in this.plugins) {
      if (this.plugins[i].mouseDown(e) === false) {
        val = false;
      }
    }
    return val;
  },

  fireKeyDown: function(e) {
    var val = true;
    for (var i in this.plugins) {
      if (this.plugins[i].keyDown(e) === false) {
        val = false;
      }
    }
    return val;
  },

  fireKeyPress: function(e) {
    var val = true;
    for (var i in this.plugins) {
      if (this.plugins[i].keyPress(e) === false) {
        val = false;
      }
    }
    return val;
  },

  fireEnabled: function(enabled) {
    for (var i in this.plugins) {
      this.plugins[i].setEnabled(enabled);
    }
  },

  fireDisabled: function(disabled) {
    for (var i in this.plugins) {
      this.plugins[i].setDisabled(disabled);
    }
  },

  fireCaretUpdated: function() {
    for (var i in this.plugins) {
      if (this.plugins[i].caretUpdated) {
        this.plugins[i].caretUpdated();
      }
    }
  }
};

exports._plugin = {};
exports.IcePluginManager = IcePluginManager;

}).call(this.ice);

(function() {

var exports = this, IceAddTitlePlugin;
  
IceAddTitlePlugin = function(ice_instance) {
  this._ice = ice_instance;
};

IceAddTitlePlugin.prototype = {
  nodeCreated: function(node, option) {
    node.setAttribute('title', (option.action || 'Modified') + ' by ' + node.getAttribute(this._ice.userNameAttribute)
        + ' - ' + ice.dom.date('m/d/Y h:ia', parseInt(node.getAttribute(this._ice.timeAttribute))));
  }
};

ice.dom.noInclusionInherits(IceAddTitlePlugin, ice.IcePlugin);
exports._plugin.IceAddTitlePlugin = IceAddTitlePlugin;

}).call(this.ice);

(function() {

var exports = this, IceCopyPastePlugin;

IceCopyPastePlugin = function(ice_instance) {
  this._ice = ice_instance;
  this._tmpNode = null;
  this._tmpNodeTagName = 'icepaste';
  this._pasteId = 'icepastediv';
  var self = this;

  // API

  // 'formatted' - paste will be MS Word cleaned.
  // 'formattedClean' - paste will be MS Word cleaned, insert and
  //    delete tags will be removed keeping insert content in place,
  //    and tags not found in `preserve` will be stripped.
  this.pasteType = 'formattedClean';

  // Subset of tags that will not be stripped when pasteType
  // is set to 'formattedClean'. Parameter is of type string with
  // comma delimited tag and attribute definitions. For example:
  //   'p,a[href],i[style|title],span[*]'
  // Would allow `p`, `a`, `i` and `span` tags. The attributes for
  // each one of these tags would be cleaned as follows: `p` tags
  // would have all attributes removed, `a` tags will have all but
  // `href` attributes removed, `i` tags will have all but `style`
  // and `title` attributes removed, and `span` tags will keep all attributes.
  this.preserve = 'p';

  // Callback triggered before any paste cleaning happens
  this.beforePasteClean = function(body) { return body; };

  // Callback triggered at the end of the paste cleaning
  this.afterPasteClean = function(body) { return body; };

  // Event Listener for copying
  ice_instance.element.oncopy = function() { return self.handleCopy.apply(self); };
};

IceCopyPastePlugin.prototype = {

  setSettings: function(settings) {
    settings = settings || {};
    ice.dom.extend(this, settings);

    this.preserve += ',' + this._tmpNodeTagName;
    this.setupPreserved();
  },

  keyDown: function(e) {
    if (e.metaKey !== true && e.ctrlKey !== true)
      return;
    if (e.keyCode == 86)
      this.handlePaste();
    else if (e.keyCode == 88)
      this.handleCut();
    return true;
  },

  handleCopy: function(e) {},

  // Inserts a temporary placeholder for the current range and removes
  // the contents of the ice element body and calls a paste handler.
  handlePaste: function(e) {

    var range = this._ice.getCurrentRange();

    if (!range.collapsed) {
      if (this._ice.isTracking) {
        this._ice.deleteContents();
        range = range.cloneRange();
      } else {
        range.deleteContents();
        range.collapse(true);
      }
    }

    if (this._ice.isTracking)
      this._ice._moveRangeToValidTrackingPos(range);

    if (range.startContainer == this._ice.element) {
      // Fix a potentially empty body with a bad selection
      var firstBlock = ice.dom.find(this._ice.element, this._ice.blockEl)[0];
      if(!firstBlock) {
        firstBlock = ice.dom.create('<' + this._ice.blockEl + ' ><br/></' + this._ice.blockEl + '>');
        this._ice.element.appendChild(firstBlock);
      }
      range.setStart(firstBlock, 0);
      range.collapse(true);
      this._ice.env.selection.addRange(range);
    }

    this._tmpNode = this._ice.env.document.createElement(this._tmpNodeTagName);
    range.insertNode(this._tmpNode);

    switch (this.pasteType) {
      case 'formatted':
        this.setupPaste();
        break;
      case 'formattedClean':
        this.setupPaste(true);
        break;
    }

    return true;
  },

  // Create a temporary div and set focus to it so that the browser can paste into it.
  // Set a timeout to push a paste handler on to the end of the execution stack.
  setupPaste: function(stripTags) {
    var div = this.createDiv(this._pasteId),
        self = this,
        range = this._ice.getCurrentRange();

    range.selectNodeContents(div);
    this._ice.selection.addRange(range);

    div.onpaste = function(event) {
      setTimeout(function(){
        self.handlePasteValue(stripTags);
      },0);
       event.stopPropagation();
    };

    div.focus();
    return true;
  },

  // By the time we get here, the pasted content will already be in the body. Extract the
  // paste, format it, remove any Microsoft or extraneous tags outside of `this.preserve`
  // and merge the pasted content into the original fragment body.
  handlePasteValue: function(stripTags) {
    // Get the pasted content.
    var doc = this._ice.env.document,
        pasteDiv = doc.getElementById(this._pasteId),
        html = ice.dom.getHtml(pasteDiv),
        childBlocks = ice.dom.children('<div>' + html + '</div>', this._ice.blockEl);
    if(childBlocks.length === 1 && ice.dom.getNodeTextContent('<div>' + html + '</div>') === ice.dom.getNodeTextContent(childBlocks)) {
      html = ice.dom.getHtml(html);
    }

    html = this.beforePasteClean.call(this, html);

    if(stripTags) {

      // Strip out change tracking tags.
      html = this._ice.getCleanContent(html);
      html = this.stripPaste(html);
    }

    html = this.afterPasteClean.call(this, html);
    html = ice.dom.trim(html);
    var range = this._ice.getCurrentRange();
    range.setStartAfter(this._tmpNode);
    range.collapse(true);

    var innerBlock = null, lastEl = null, newEl = null;
    var fragment = range.createContextualFragment(html);
    var changeid = this._ice.startBatchChange();

    // If fragment contains block level elements, most likely we will need to
    // do some splitting so we do not have P tags in P tags, etc. Split the
    // container from current selection and then insert paste contents after it.
    if(ice.dom.hasBlockChildren(fragment)) {
      // Split from current selection.
      var block = ice.dom.isChildOfTagName(this._tmpNode, this._ice.blockEl);
      range.setEndAfter(block.lastChild);
      this._ice.selection.addRange(range);
      var contents = range.extractContents();
      var newblock = doc.createElement(this._ice.blockEl);
      newblock.appendChild(contents);
      ice.dom.insertAfter(block, newblock);

      range.setStart(newblock, 0);
      range.collapse(true);
      this._ice.selection.addRange(range);
      var prevBlock = range.startContainer;

      // Paste all of the children in the fragment.
      while(fragment.firstChild) {
        if(fragment.firstChild.nodeType === 3 && !jQuery.trim(fragment.firstChild.nodeValue)) {
          fragment.removeChild(fragment.firstChild);
          continue;
        }
        // We may have blocks with text nodes at the beginning or end. For example, this paste:
        //  textnode <p>blocktext</p> <p>blocktext</p> moretext
        // In which case we wrap the leading or trailing text nodes in blocks.
        if(ice.dom.isBlockElement(fragment.firstChild)) {
          if(fragment.firstChild.textContent !== "") {
            innerBlock = null;
            var insert = null;
            if(this._ice.isTracking) {
              insert = this._ice.createIceNode('insertType');
              this._ice.addChange('insertType', [insert]);
              newEl = doc.createElement(fragment.firstChild.tagName);
              insert.innerHTML = fragment.firstChild.innerHTML;
              newEl.appendChild(insert);
            } else {
              insert = newEl = doc.createElement(fragment.firstChild.tagName);
              newEl.innerHTML = fragment.firstChild.innerHTML;
            }
            lastEl = insert;
            ice.dom.insertBefore(prevBlock, newEl);
          }
          fragment.removeChild(fragment.firstChild);
        } else {
          if(!innerBlock) {
            // Create a new block and append an insert
            newEl = doc.createElement(this._ice.blockEl);
            ice.dom.insertBefore(prevBlock, newEl);
            if(this._ice.isTracking) {
              innerBlock = this._ice.createIceNode('insertType');
              this._ice.addChange('insertType', [innerBlock]);
              newEl.appendChild(innerBlock);
            } else {
              innerBlock = newEl;
            }
          }
          lastEl = innerBlock;
          innerBlock.appendChild(fragment.removeChild(fragment.firstChild));
        }
      }
      if (!newblock.textContent) {
        newblock.parentNode.removeChild(newblock);
      }

    } else {
      if(this._ice.isTracking) {
        newEl = this._ice.createIceNode('insertType', fragment);
        this._ice.addChange('insertType', [newEl]);
        range.insertNode(newEl);
        lastEl = newEl;
      } else {
        var child;
        while((child = fragment.firstChild)) {
          range.insertNode(child);
          range.setStartAfter(child);
          range.collapse(true);
          lastEl = child;
        }
      }
    }
    this._ice.endBatchChange(changeid);
    pasteDiv.parentNode.removeChild(pasteDiv);
    this._cleanup(lastEl);
  },


  createDiv: function(id) {
    var doc = this._ice.env.document, // Document object of window or tinyMCE iframe
        oldEl = doc.getElementById(id);
    if(oldEl) {
      ice.dom.remove(oldEl);
    }

    var div = doc.createElement('div');
    div.id = id;
    div.setAttribute('contentEditable', true);
    ice.dom.setStyle(div, 'width', '1px');
    ice.dom.setStyle(div, 'height', '1px');
    ice.dom.setStyle(div, 'overflow', 'hidden');
    ice.dom.setStyle(div, 'position', 'fixed');
    ice.dom.setStyle(div, 'top', '10px');
    ice.dom.setStyle(div, 'left', '10px');

    div.appendChild(doc.createElement('br'));
    doc.body.appendChild(div);
    return div;
  },

  // Intercepts cut operation and handles by creating an editable div, copying the current selection
  // into it, deleting the current selection with track changes, and selecting the contents in the
  // editable div.
  handleCut: function() {
    var self = this,
        range = this._ice.getCurrentRange();
    if (range.collapsed) return; // If nothing is selected, there's nothing to mark deleted

    this.cutElement = this.createDiv('icecut');
    // Chrome strips out spaces between text nodes and elements node during cut
    this.cutElement.innerHTML = range.getHTMLContents().replace(/ </g, '&nbsp;<').replace(/> /g, '>&nbsp;');

    if (this._ice.isTracking) this._ice.deleteContents();
    else range.deleteContents();

    var crange = this._ice.env.document.createRange();
    crange.setStart(this.cutElement.firstChild, 0);
    crange.setEndAfter(this.cutElement.lastChild);

    setTimeout(function() {
      self.cutElement.focus();

      // After the browser cuts out of the `cutElement`, reset the range and remove the cut element.
      setTimeout(function() {
        ice.dom.remove(self.cutElement);
        range.setStart(range.startContainer, range.startOffset);
        range.collapse(false);
        self._ice.env.selection.addRange(range);
      }, 100);
    }, 0);

    self._ice.env.selection.addRange(crange);
  },


  // Strips ice change tracking tags, Microsoft Word styling/content, and any
  // tags and attributes not found in `preserve` from the given `content`.
  stripPaste: function(content) {
    // Clean word stuff out and strip tags that are not in `this.preserve`.
    content = this._cleanWordPaste(content);
    content = this.cleanPreserved(content);
    return content;
  },

  // Parses `preserve` to setup `_tags` with a comma delimited list of all of the
  // defined tags, and the `_attributesMap` with a mapping between the allowed tags and
  // an array of their allowed attributes. For example, given this value:
  //   `preserve` = 'p,a[href|class],span[*]'
  // The following will result:
  //   `_tags` = 'p,a,span'
  //   `_attributesMap` = ['p' => [], 'a' => ['href', 'class'], 'span' => ['*']]
  setupPreserved: function() {
    var self = this;
    this._tags = '';
    this._attributesMap = [];

    ice.dom.each(this.preserve.split(','), function(i, tagAttr) {
      // Extract the tag and attributes list
      tagAttr.match(/(\w+)(\[(.+)\])?/);
      var tag = RegExp.$1;
      var attr = RegExp.$3;

      if(self._tags) self._tags += ',';
      self._tags += tag.toLowerCase();
      self._attributesMap[tag] = attr.split('|');
    });
  },

  // Cleans the given `body` by removing any tags not found in `_tags` and replacing them with
  // their inner contents, and removes attributes from any tags that aren't mapped in `_attributesMap`.
  cleanPreserved: function(body) {
    var self = this;
    var bodyel = this._ice.env.document.createElement('div');
    bodyel.innerHTML = body;

    // Strip out any tags not found in `this._tags`, replacing the tags with their inner contents.
    bodyel = ice.dom.stripEnclosingTags(bodyel, this._tags);

    // Strip out any attributes from the allowed set of tags that don't match what is in the `_attributesMap`
    ice.dom.each(ice.dom.find(bodyel, this._tags), function(i, el) {
      if (ice.dom.hasClass(el, 'skip-clean')) {
        return true;
      }
      var tag = el.tagName.toLowerCase();
      var attrMatches = self._attributesMap[tag];

      // Kleene star - keep all of the attributes for this tag.
      if(attrMatches[0] && attrMatches[0] === '*')
        return true;

      // Remove any foreign attributes that do not match the map.
      if(el.hasAttributes()) {
        var attributes = el.attributes;
        for(var i = attributes.length - 1; i >= 0; i--) {
          if(!ice.dom.inArray(attributes[i].name, attrMatches)) {
            el.removeAttribute(attributes[i].name);
          }
        }
      }
    });
    return bodyel.innerHTML;
  },

  _cleanWordPaste: function(content) {
    // Meta and link tags.
    content = content.replace(/<(meta|link)[^>]+>/g, "");

    // Comments.
    content = content.replace(/<!--(.|\s)*?-->/g, '');

    // Remove style tags.
    content = content.replace(/<style>[\s\S]*?<\/style>/g, '');

    // Remove span and o:p etc. tags.
    //content = content.replace(/<\/?span[^>]*>/gi, "");
    content = content.replace(/<\/?\w+:[^>]*>/gi, '' );

    // Remove XML tags.
    content = content.replace(/<\\?\?xml[^>]*>/gi, '');

    // Generic cleanup.
    content = this._cleanPaste(content);

    // Remove class, lang and style attributes.
    content = content.replace(/<(\w[^>]*) (lang)=([^ |>]*)([^>]*)/gi, "<$1$4");

    return content;
  },

  _cleanPaste: function(content) {
    // Some generic content cleanup. Change all b/i tags to strong/em.
    content = content.replace(/<b(\s+|>)/g, "<strong$1");
    content = content.replace(/<\/b(\s+|>)/g, "</strong$1");
    content = content.replace(/<i(\s+|>)/g, "<em$1");
    content = content.replace(/<\/i(\s+|>)/g, "</em$1");
    return content;
  },

  _cleanup: function(moveTo) {
    try {
      moveTo = moveTo && moveTo.lastChild || moveTo || this._tmpNode;
      // Move the range to the end of moveTo so that the cursor will be at the end of the paste.
      var range = this._ice.getCurrentRange();
      range.setStartAfter(moveTo);
      range.collapse(true);
      this._ice.selection.addRange(range);

      // Kill the tmp node.
      this._tmpNode.parentNode.removeChild(this._tmpNode);
      this._tmpNode = null;
      // Kill any empty change nodes.
      var ins = this._ice.env.document.getElementsByClassName(this._ice.changeTypes['insertType'].alias);
      for(var i = 0; i < ins.length; i++) {
        if(!ins[i].textContent) {
          if(ins[i].parentNode) {
            ins[i].parentNode.removeChild(ins[i]);
          }
        }
      }
    } catch(e) {
      window.console && console.error(e);
    }
  }
};

ice.dom.noInclusionInherits(IceCopyPastePlugin, ice.IcePlugin);
exports._plugin.IceCopyPastePlugin = IceCopyPastePlugin;

}).call(this.ice);

(function() {

var exports = this, ice = this.ice;

var IceSmartQuotesPlugin = function(ice_instance) {
  this._ice = ice_instance;
};

IceSmartQuotesPlugin.prototype = {

  /**
   * Finds each block in `element` and converts quotes into smart quotes.
   */
  convert: function(element) {
    var self = this;
    try {
      self._ice.placeholdDeletes();
      ice.dom.each(element.getElementsByTagName(this._ice.blockEl), function(i, el) {
        self._convertBlock(el);
      });
    } catch(e) {
      window.console && console.error(e);
    } finally {
      self._ice.revertDeletePlaceholders();
    }
  },
  
  // Converts the quotes in the given element to smart quotes.
  _convertBlock: function(el) {

    // If there are less than 2 characters, we don't have enough to go on.
    if (ice.dom.getNodeTextContent(el) < 2) return;

    var previous, current, next, data, html = '', getNextChar,
      regularSingle = "'",
      regularDouble = '"',
      smartSingleLeft = String.fromCharCode(8216),  // aka - open curly single quote
      smartSingleRight = String.fromCharCode(8217),   // aka - close curly single quote
      smartDoubleLeft = String.fromCharCode(8220),  // aka - open curly double quote
      smartDoubleRight = String.fromCharCode(8221),   // aka - close curly double quote
      isDigit = function(c) { return /\d/.test(c); },
      isChar = function(c) { return /\w/.test(c); },
      isSpace = function(c) { return c === String.fromCharCode(160) || c === String.fromCharCode(32); },
      isStartChar = function(c) { return isSpace(c) || c === '('; },
      isEndChar = function(c) { return isSpace(c) || c == null || c === ';' || c === ')' || c == '.' || c === '!' || c === ',' || c === '?' || c === ':'; },
      isNonSpace = function(c) { return !isSpace(c); },
      isDouble = function(c) { return c === regularDouble || c === smartDoubleLeft || c === smartDoubleRight; },
      isSingle = function(c) { return c === regularSingle || c === smartSingleLeft || c === smartSingleRight; };

    // Split the html into array allocations with the following criteria:
    //   html tags: starts with "<" and ends with ">"
    //   html entities: starts with "&" and ends with ";"
    //   characters: any character outside of an html tag or entity
    // So the following html:
    //   n&ce <b id="bold">test</b>
    // Would split into the following array:
    //  ['n', '&amp;', 'c', 'e', ' ', '<b id="bold">', 't', 'e', 's', 't', '</b>'];
    data = ice.dom.getHtml(el).match(/(<("[^"]*"|'[^']*'|[^'">])*>|&.*;|.)/g);

    // Searches through the `data` array from the given index a given number of
    // characters forward or backward and returns the found character.
    getNextChar = function(data, fromIndex, nCharacters) {
      var dLength = data.length,
        addWith = nCharacters < 0 ? -1 : 1;
    
      return (function getChar(data, fromIndex, nCharacters) {
        // Base case - did we move outside of the bounds of the data array?
        if (fromIndex < 0 || fromIndex >= dLength) return null;
        
        var next = data[fromIndex + addWith];

        // If we find a character and we have moved through the
        // nCharacters, then the recursion is done.
        if (next && next.length == 1) {
          nCharacters += (addWith * -1);
          if (!nCharacters) return next;
        }
        return getChar(data, fromIndex + addWith, nCharacters);

      })(data, fromIndex, nCharacters);
    };

    ice.dom.each(data, function(pos, val) {
      // Convert space entities so that they can be processed as normal characters.
      if (val == '&nbsp;') val = data[pos] = ' ';

      // If the val is a character, then examine the surroundings
      // and convert smart quotes, if necessary.
      if (val.length == 1) {
        
        // Keep convenience pointers to the previous, current and next characters.
        previous = getNextChar(data, pos, -1);
        current = val;
        next = getNextChar(data, pos, 1);

        switch (current) {
          
          /**
           * Conversion Rules:
           * ----------------
           * 
           * START: assign smart left/open
           *   [SPACE|START_PARENTHESIS]'word
           *   [SPACE|START_PARENTHESIS]"word
           * 
           * END: assign smart right/close
           *   word'[SPACE|SEMICOLON|COLON|PERIOD|COMMA|EXCLAMATION_MARK|QUESTION_MARK|END_PARENTHESIS|NULL]
           *   word"[SPACE|SEMICOLON|COLON|PERIOD|COMMA|EXCLAMATION_MARK|QUESTION_MARK|END_PARENTHESIS|NULL]
           * 
           * PLURAL_CONTRACTION: assign smart right/close
           *   Matt's
           *   can't
           *   O'Reilly
           * 
           * YEAR_ABBREVIATION: assign smart right/close
           *   [SPACE|NULL]'99[SPACE|SEMICOLON|COLON|PERIOD|COMMA|EXCLAMATION_MARK|QUESTION_MARK|END_PARENTHESIS|NULL]
           * 
           * NESTED_START: assign smart left/open
           *   [SPACE|NULL]"[SPACE]'word
           * 
           * NESTED_END: assign smart left/open
           *   word'[SPACE]"[SPACE|SEMICOLON|COLON|PERIOD|COMMA|EXCLAMATION_MARK|QUESTION_MARK|END_PARENTHESIS|NULL]
           * 
           * Notes:
           *  - The following will not be converted correctly - ...word 'Til Death - it should
           *  get a right/close smart quote, but will get a left/open.
           *  - Distinguishing between year abbreviation, '99, and when to use an open single quote
           *  could fail if a single quoted region starts with a double digit number - '99 problems'
           *  - Since they are a rare case and there are many permutations, measurements are not being
           *  handled (6'8", 6' 8", 6', 8").
           */

          // Convert smart single quotes to non-smart quote and fall through to single quote 
          // handling, in case the context has changed and we need to update the smart quote.
          case smartSingleLeft:
          case smartSingleRight:
            current = regularSingle;
          case regularSingle:
            // YEAR_ABBREVIATION - look 2 ahead to see if there are two digits in a row - not fool proof
            if ((previous == null || isSpace(previous)) && isDigit(next) && isDigit(getNextChar(data, pos, 2)) && isEndChar(getNextChar(data, pos, 3)))
              current = smartSingleRight;
            // START
            else if (previous == null || (isStartChar(previous) && isNonSpace(next)))
              current = smartSingleLeft;
            // END
            else if (next == null || (isNonSpace(previous) && isEndChar(next)))
              current = smartSingleRight;
            // PLURAL_CONTRACTION
            else if (isChar(previous) && isChar(next))
              current = smartSingleRight;
            break;
          
          // Convert smart double quotes to non-smart quote and fall through to double quote 
          // handling, in case the context has changed and we need to update the smart quote.
          case smartDoubleLeft:
          case smartDoubleRight:
            current = regularDouble;
          case regularDouble:
            // NESTED_END
            if (isEndChar(next) && isSpace(previous) && isSingle(getNextChar(data, pos, -2)))
              current = smartDoubleRight;
            // START
            else if (previous == null || (isStartChar(previous) && isNonSpace(next)))
              current = smartDoubleLeft;
            // END
            else if (next == null || (isNonSpace(previous) && isEndChar(next)))
              current = smartDoubleRight;
            // NESTED_START
            else if ((previous == null || isSpace(previous)) && (isSpace(next) && isSingle(getNextChar(data, pos, 1))))
              current = smartDoubleLeft;
            break;
        }
        if (current != null) data[pos] = current;
      }
    });
    
    ice.dom.setHtml(el, data.join(''));
  }
};

ice.dom.noInclusionInherits(IceSmartQuotesPlugin, ice.IcePlugin);
exports.ice._plugin.IceSmartQuotesPlugin = IceSmartQuotesPlugin;

}).call(this);
(function() {

var exports = this;

/**
 * When active, this plugin will convert two successively typed dashes, within
 * the ice block element, into an emdash. 
 */
var IceEmdashPlugin = function(ice_instance) {
	this._ice = ice_instance;
};

IceEmdashPlugin.prototype = {

	keyDown: function(e) {
		// Catch dashes.
		if (ice.dom.isBrowser('mozilla')) {
      var version = parseInt(ice.dom.browser().version);
      if ((version > 14 && e.keyCode === 173) || (version <= 14 && e.keyCode === 109)) {
        return this.convertEmdash(e);
      }
		} else if (e.keyCode === 189) {
			return this.convertEmdash(e);
		}
		return true;
	},
	
	convertEmdash: function(e) {
		var range = this._ice.getCurrentRange();
		if(range.collapsed) {
			try {
				// Move the start back one character so we can enclose the range around the previous character to check if it is a dash
				range.moveStart(ice.dom.CHARACTER_UNIT, -1);
				// Get the parent block element for the start and end containers
				var startBlock = ice.dom.getParents(range.startContainer, this._ice.blockEl)[0];
				var endBlock = ice.dom.getParents(range.endContainer, this._ice.blockEl)[0];
				// Make sure that the start and end containers aren't in different blocks, or that the start isn't in a delete.
				if(startBlock === endBlock && !this._ice.getIceNode(range.startContainer, 'deleteType')) {
					// Get the last character and check to see if it is a dash.
					c = range.toHtml();
					if(c === '-') {
						// Extract the last character/dash and insert an emdash
						range.extractContents();
						range.collapse();
						var mdash = this._ice.env.document.createTextNode('\u2014');
						if (this._ice.isTracking) {
							this._ice._insertNode(mdash, range);
						} else {
							range.insertNode(mdash);
							range.setStart(mdash, 1);
							range.collapse(true);
						}
						this._ice._preventKeyPress = true;
						return false;
					}
				}
			} catch(e) {}
			range.collapse();
		}
		return true;
	}

};

ice.dom.noInclusionInherits(IceEmdashPlugin, ice.IcePlugin);
exports._plugin.IceEmdashPlugin = IceEmdashPlugin;

}).call(this.ice);
