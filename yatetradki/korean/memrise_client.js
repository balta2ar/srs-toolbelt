// ==UserScript==
// @name         Upload audio to Memrise
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Automatically finds words without audios in memrise course and uploads the audio
// @author       balta2ar
// @match        https://www.memrise.com/course/*/edit/*
// @require      http://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

    /**
     * Display error if an AJAX request fails.
     * @param {string} prefix Prefix to add before the error message.
     * @param {object} response Problematic response.
     */
    function showError(prefix, response) {
        var msg = prefix + ": an error occurred." +
            "\nresponseText: " + response.responseText +
            "\nreadyState: " + response.readyState +
            "\nresponseHeaders: " + response.responseHeaders +
            "\nstatus: " + response.status +
            "\nstatusText: " + response.statusText +
            "\nfinalUrl: " + response.finalUrl;
        console.log(msg);
    }

    /**
     * Universal method that performs AJAX call.
     * @param {string} method 'GET' or 'POST'.
     * @param {string} url URL to access.
     * @param {function} callback Function to call upon success.
     * @param {object} headers Additional headers.
     * @param {object} data AJAX data to pass with the request.
     */
    function callAjax(method, url, callback, headers, data){
        var query = {
            method: method, //"POST", // GET
            url: url,
            synchronous: true,
            onload: function(response) {
                //alert('onload RECEIVED' + response.responseText);
                try {
                    callback(JSON.parse(response.responseText));
                } catch (e) {
                    console.log('onload RECEIVED' + response.responseText);
                    console.log(e);
                }
            },
            onerror: function(response) {
                showError("callAjax onerror", response);
                console.log(query);
            },
        };
        if (headers) {
            query.headers = headers;
        }
        if (data) {
            query.data = data;
        }
        GM_xmlhttpRequest(query);
    }

    /**
     * Rertrieve audio for the given word. Calls `onsuccess` upon success.
     * @param {string} word Word to get audio for.
     * @param {function} onsuccess Callback to call on success.
     */
    function getAudioForWord(word, onsuccess) {
        callAjax("GET",
                //  "http://localhost:5000/api/get_audio/" + encodeURIComponent(word),
                 "https://localhost:5000/api/get_audio/" + encodeURIComponent(word),
                 onsuccess,
                 null,
                 null);
    }

    /**
     * Convert result returned by memrise_server.py into a blob. memrise_server
     * returns result in a base64 format. It should be decoded and converted
     * into a Blob, to be used in FormData later.
     * @param result Result from memrise_server.
     @ @return Blob that is ready to be used in FormData.
     */
    function resultToBlob(result) {
        MEMRISE.RESULT = result;
        var byteString = atob(result.base64_data);
        var mimeString = 'audio/mp3';

        var ab = new ArrayBuffer(byteString.length);
        var ia = new Uint8Array(ab);
        for (var i = 0; i < byteString.length; i++)
        {
            ia[i] = byteString.charCodeAt(i);
        }

        var bb = new Blob([ab], { "type": mimeString });
        MEMRISE.byteString = byteString;
        MEMRISE.ab = ab;
        MEMRISE.ia = ia;
        MEMRISE.bb = bb;
        return bb;
    }

    function uploadAudio(result, uploadFormParams, onsuccess) {
        // https://www.memrise.com/ajax/thing/cell/upload_file/

        var formdata = new FormData();
        for (var p in uploadFormParams) {
            formdata.append(p, uploadFormParams[p]);
        }

        var blob = resultToBlob(result);
        formdata.append('f', blob, 'sound.mp3');

        // I'm using jQuery ajax here because GM_xmlhttpRequest often
        // resulted in invalid CSRF token reply from memrise server.
        //
        // https://stackoverflow.com/questions/6974684/how-to-send-formdata-objects-with-ajax-requests-in-jquery
        var query = {
            type:        'POST',
            url:         'https://www.memrise.com/ajax/thing/cell/upload_file/',
            //dataType:   'JSON',
            data:        formdata,
            processData: false,
            contentType: false,
            //contentType: 'multipart/form-data',
            success:     function (response) {
                console.log(response);
                onsuccess(response);
            },
            error:       function(response) {
                showError("uploadAudio onerror 2", response);
                console.log(query);
                console.log(response);
                console.log(result);
            },
        };

        $.ajax(query);

        /*
        Sample requests:

        ------WebKitFormBoundary7wGHsJmxhEeD9hSN
        Content-Disposition: form-data; name="thing_id"

        129422029
        ------WebKitFormBoundary7wGHsJmxhEeD9hSN
        Content-Disposition: form-data; name="cell_id"

        3
        ------WebKitFormBoundary7wGHsJmxhEeD9hSN
        Content-Disposition: form-data; name="cell_type"

        column
        ------WebKitFormBoundary7wGHsJmxhEeD9hSN
        Content-Disposition: form-data; name="csrfmiddlewaretoken"

        ErZhxGeMIZv3RAoapqUhoezixqgdaRo8EvYlMJIiH8rAfTn1po00DvJBiYGSswfB
        ------WebKitFormBoundary7wGHsJmxhEeD9hSN
        Content-Disposition: form-data; name="f"; filename="translate_tts.mp3"
        Content-Type: audio/mp3
        */

    }

    function onUploadedSuccessfully(result, thing, buttons) {
        var wrapper = document.createElement('div');
        wrapper.innerHTML = result.rendered;

        var audioBlock = thing.children[3];
        var newAudioColumn = wrapper.children[0]; //wrapper.firstChild;
        var oldAudioColumn = audioBlock.children[0];

        audioBlock.removeChild(oldAudioColumn);
        audioBlock.appendChild(newAudioColumn);
    }

    function onWordNotFound(result, thing, buttons) {
        buttons.innerHTML = 'NOT FOUND';
    }

    function onAddAudio(word, uploadFormParams, thing, buttons) {
        //callAjax("http://localhost:5000/api/get_audio/" + encodeURIComponent(word), displayResult);
        getAudioForWord(word, function(result) {
            if (result.success) {
                console.log(result);
                uploadAudio(result, uploadFormParams, function(uploadResult) {
                    console.log('UPLOADED');
                    onUploadedSuccessfully(uploadResult, thing, buttons);
                });
            } else {
                console.error('Cound not find audio for word: ' + word);
                onWordNotFound(result, thing, buttons);
            }
        });
    }

    /**
     * Find levels and expand/collapse them (toggle, click on them).
     * @param {levelSelector} string Selector that is used to find levels.
     * @param {max_levels} int Expand not more than this number of levels.
     */
    function toggleExpandCollapseLevels(levelSelector, maxLevels) {
        // var uncollapsedLevels = document.querySelectorAll('.level:not(.collapsed)');
        var uncollapsedLevels = document.querySelectorAll(levelSelector);
        var limit = Math.min(maxLevels, uncollapsedLevels.length);

        for (var i = 0; i < limit; i++) {
            console.log('expanding: ' + i);
            var level = uncollapsedLevels[i];
            var showHideButton = level.getElementsByClassName('show-hide btn btn-small');
            showHideButton[0].click();
        }
    }

    /**
     * This function adds main buttons: Add, Remove, Expand, Collapse.
     * Add - adds audio to all words on the page that don't have an audio yet.
     * Remove - removes all audios.
     * This function also starts a reoccuring timer events that when fire,
     * tries to:
     *    1. add "ConvertToTabs" button to all bulk upload dialogs.
     *    2. find words without an audio and add "Upload" button to the button group.
     */
    function addButtons() {
        // TODO: add buttons not only to header but also to AddLevel panel
        // so that when header is removed in memrise_syncher, buttons are
        // still available.

        var header = document.querySelector('ul.header-nav');
        // <li class="header-nav-item plain ">
        // <a href="/home/" class="nav-item-btn">
        //            <span class="nav-item-btn-text">Home</span>
        var startButton = document.createElement('li');
        startButton.setAttribute('class', 'header-nav-item plain');
        //startButton.innerHTML = 'Add missing audio [bz]';
        startButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">+♫</span> </a>';
        startButton.addEventListener('click', function(event) { clickAllAddAudioButtons(); } );
        header.appendChild(startButton);

        var deleteButton = document.createElement('li');
        deleteButton.setAttribute('class', 'header-nav-item plain');
        deleteButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">&ndash;♫</span> </a>';
        deleteButton.addEventListener('click', function(event) { clickAllDeleteButtons(); } );
        header.appendChild(deleteButton);

        var MAX_EXPAND = 5;
        var SELECTOR_COLLAPSED = '.level.collapsed';
        var SELECTOR_EXPANDED = '.level:not(.collapsed)';

        var expandButton = document.createElement('li');
        expandButton.setAttribute('class', 'header-nav-item plain');
        expandButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">&lt;' + MAX_EXPAND + '&gt;</span> </a>';
        expandButton.addEventListener('click', function(event) { toggleExpandCollapseLevels(SELECTOR_COLLAPSED, MAX_EXPAND); } );
        header.appendChild(expandButton);

        var collapseButton = document.createElement('li');
        collapseButton.setAttribute('class', 'header-nav-item plain');
        collapseButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">&gt;' + MAX_EXPAND + '&lt;</span> </a>';
        collapseButton.addEventListener('click', function(event) { toggleExpandCollapseLevels(SELECTOR_EXPANDED, MAX_EXPAND); } );
        header.appendChild(collapseButton);

        //var bulkAddButton = document.createElement('li');
        //bulkAddButton.setAttribute('class', 'header-nav-item plain');
        //bulkAddButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">Bulk add</span> </a>';
        //bulkAddButton.addEventListener('click', function(event) { alert("BULK ADD NOT IMPLEMENTED"); } );
        //header.appendChild(bulkAddButton);

        setInterval(function() { tryAddConvertToTabs(); }, 1000);
        setInterval(function() { findMissingAndAddUpload(); }, 1000);
    }

    /**
     * This function is trying to find a tag that has matching text withing
     * a given container.
     * @param container {DOMElement} DOM element to search in.
     * @param tagName <tag_name> to search for.
     * @param text Text to search for.
     @ @return DOMElement if found, null otherwise.
     */
    function findLastTagWithText(container, tagName, text) {
        var aTags = container.getElementsByTagName(tagName);
        var searchText = text;
        var result = null;

        for (var i = 0; i < aTags.length; i++) {
            if (aTags[i].textContent == searchText) {
                result = aTags[i];
            }
        }
        return result;
    }

    /**
     * This function locates all textareas in the document, breaks the input
     * into lines, and replaces first tabular character in each line with a ";"
     * (semicolon). It's helpful because I prefer to keep new words in my
     * memos in the format as follows:
     * <korean_word>; translation; more comments; etc...
     */
    function onConvertTabs() {
        var textareas = document.querySelectorAll('textarea');
        if (!textareas) {
            console.log("textareas not found");
            return;
        }

        for (var index = 0; index < textareas.length; index++) {
            var textarea = textareas[index];

            // We need to process each line separately as we only need
            // to replace the first occurence of \t in each line.
            var lines = textarea.value.match(/[^\r\n]+/g);
            try {
                for (var i = 0; i < lines.length; i++) {
                    lines[i] = lines[i].replace(/;/, '\t');
                }
                lines = lines.join('\n');
                textarea.value = lines;
            } catch (e) {
                console.log(e);
            }

        }
        console.log("converted text to tabs");
    }

    /**
     * Try to find all dialogs with "Add" button and append "ConvertToTabs".
     */
    function tryAddConvertToTabs() {
        var addButton = findLastTagWithText(document, "a", "Add");
        if (addButton) {
            //console.log("FOUND add button");
            var convertTabsButton = findLastTagWithText(addButton.parentNode, "a", "ConvertTabs");
            if (convertTabsButton) {
                //console.log("FOUND convert tabs button");
            } else {
                // class="btn column-editor-close"
                convertTabsButton = document.createElement('a');
                convertTabsButton.setAttribute('class', 'btn');
                convertTabsButton.innerHTML = 'ConvertTabs';
                convertTabsButton.addEventListener('click', function(event) { onConvertTabs(); } );
                addButton.parentNode.appendChild(convertTabsButton);
                console.log("ADDED convert tabs button");
            }
        }
    }

    /**
     * Add Upload button for one thing. Thing is a row in Memrise table.
     * It contains a word, translation, and and a block with audio buttons.
     * This function adds HTML code of a an Add button into the page.
     * @param thing Thing (row) to add Upload button to.
     * @return true if successfully added Upload button.
     */
    function addUploadButtonForThing(thing) {
        var buttons = thing.querySelector('button.btn.btn-mini.dropdown-toggle.disabled');

        if (buttons === null) {
            return false;
        }

        var buttonGroup = buttons.parentNode;

        // is there already add button?
        var addAudioButton = findLastTagWithText(buttonGroup.parentNode, "div", "AddAudio");
        if (addAudioButton) {
            return false;
        }

        var firstElement = buttons.parentNode.parentNode.parentNode.getElementsByClassName('text')[0];
        var word = firstElement.innerText.trim().replace(/\//, '_');
        var thingId = thing.getAttribute('data-thing-id');

        var uploadFormParams = {
            thing_id: thingId,
            cell_id: "3",
            cell_type: "column",
            csrfmiddlewaretoken: MEMRISE.csrftoken
        };

        var customUploadButton = document.createElement('div');
        //<div class="btn btn-mini open-recorder">Record</div>

        // I use additional class "btn-bz-add-audio" to make it easier
        // to find these buttons later in memrise_syncher when adding
        // pronunciation automatically.
        customUploadButton.setAttribute('class', 'btn btn-mini btn-bz-add-audio');
        customUploadButton.setAttribute('title', 'AddAudio');
        //customUploadButton.setAttribute('onclick', 'onAddAudio(' + word + ')');
        customUploadButton.addEventListener('click', function(event) {
            onAddAudio(word, uploadFormParams, thing, buttons);
        });
        // onAddAudio(word, uploadFormParams, thing, buttons);
        customUploadButton.innerHTML = 'AddAudio';

        buttonGroup.appendChild(customUploadButton);

        //callAjax("http://localhost:5000/api/get_audio/" + encodeURIComponent(word), displayResult);
        return true;
    }

    /**
     * Click all Delete buttons to remove audio from all words that are
     * visible on the page.
     */
    function clickAllDeleteButtons() {
        var deleteButtons = document.querySelectorAll('[title="Delete this audio file"]');
        for (var i = 0; i < deleteButtons.length; i++) {
            var deleteButton = deleteButtons[i];
            deleteButton.click();
        }
    }

    /**
     * Click all Add buttons to automatically retrieve audio from
     * memrise_server for all the words.
     */
    function clickAllAddAudioButtons() {
        var addAudioButtons = document.querySelectorAll('[title="AddAudio"]');
        for (var i = 0; i < addAudioButtons.length; i++) {
            var addAudioButton = addAudioButtons[i];
            addAudioButton.click();
        }
    }

    /**
     * Scan all words in the table, find those who are missing audios and
     * append Upload button to each one of them.
     */
    function findMissingAndAddUpload() {
        var things = document.getElementsByClassName('thing');
        for (var i = 0; i < things.length; i++) {

            if (i >= 9999) {
                break;
            }

            var thing = things[i];
            if (addUploadButtonForThing(thing)) {
                //break;
            }
        }
    }

    // Add all main buttons after a while
    setTimeout(function() { addButtons(); }, 1000);
})();
