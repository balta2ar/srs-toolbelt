// ==UserScript==
// @name         Upload audio to Memrise
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Automatically finds words without audios in memrise course and uploads the audio
// @author       balta2ar
// @match        https://www.memrise.com/course/1344980/baltazar-korean-words/edit/*
// @require      http://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

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

    function callAjax(method, url, callback, headers, data){
        //alert("START");

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
        // console.log(query);
        GM_xmlhttpRequest(query);
        //alert("END");
    }

    function getAudioForWord(word, onsuccess) {
        callAjax("GET",
                 "http://localhost:5000/api/get_audio/" + encodeURIComponent(word),
                 onsuccess,
                 null,
                 null);
    }

    function resultToBlob(result) {
        //window.RESULT = result;
        MEMRISE.RESULT = result;
        //alert(result['base64_data']);
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

    //function displayResult(result) {
    function uploadAudio(result, uploadFormParams, onsuccess) {
        // https://www.memrise.com/ajax/thing/cell/upload_file/

        var formdata = new FormData();
        for (var p in uploadFormParams) {
            formdata.append(p, uploadFormParams[p]);
        }

        //var formData = new FormData();
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
        return;

        /*
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

        var query = {
            method: "POST",
            url: "https://www.memrise.com/ajax/thing/cell/upload_file/",
            onload: function (response) {
                console.log('UPLOAD RESULT:' + response.responseText);
                onsuccess(response.responseText);
            },
            onerror: function(response) {
                showError("uploadAudio onerror 2", response);
                console.log(query);
                console.log(response);
                console.log(result);
            },
        };

        query.data = new FormData();
        for (var p in uploadFormParams) {
            query.data.append(p, uploadFormParams[p]);
        }

        //var formData = new FormData();
        var blob = resultToBlob(result);
        query.data.append('f', blob, 'sound.mp3');

        GM_xmlhttpRequest(query);

        //query.headers = {"Content-Type": "multipart/form-data"};
        //var params = {
        //    thing_id: "query",
        //    cell_id: "3",
        //    cell_type: "column",
        //    csrfmiddlewaretoken: MEMRIZE.csrftoken,
        //};

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
        //alert("ADDING AUDIO FOR WORD " + word);
        //callAjax("http://localhost:5000/api/get_audio/" + encodeURIComponent(word), displayResult);
        getAudioForWord(word, function(result) {
            //alert(JSON.stringify(result));
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

    function addButtons() {
        var header = document.querySelector('ul.header-nav');
        // <li class="header-nav-item plain ">
        // <a href="/home/" class="nav-item-btn">
        //            <span class="nav-item-btn-text">Home</span>
        var startButton = document.createElement('li');
        startButton.setAttribute('class', 'header-nav-item plain');
        //startButton.innerHTML = 'Add missing audio [bz]';
        startButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">Add ♫</span> </a>';
        startButton.addEventListener('click', function(event) { clickAllAddAudioButtons(); } );
        header.appendChild(startButton);

        var deleteButton = document.createElement('li');
        deleteButton.setAttribute('class', 'header-nav-item plain');
        deleteButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">Delete ♫</span> </a>';
        deleteButton.addEventListener('click', function(event) { clickAllDeleteButtons(); } );
        header.appendChild(deleteButton);

        //var bulkAddButton = document.createElement('li');
        //bulkAddButton.setAttribute('class', 'header-nav-item plain');
        //bulkAddButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">Bulk add</span> </a>';
        //bulkAddButton.addEventListener('click', function(event) { alert("BULK ADD NOT IMPLEMENTED"); } );
        //header.appendChild(bulkAddButton);

        setInterval(function() { tryAddConvertToTabs(); }, 1000);
        setInterval(function() { findMissingAndAddUpload(); }, 1000);
    }

    function findLastTagWithText(container, tagName, text) {
        var aTags = container.getElementsByTagName(tagName);
        var searchText = text;
        var result = null;

        for (var i = 0; i < aTags.length; i++) {
            if (aTags[i].textContent == searchText) {
                // result.push(aTags[i]);
                result = aTags[i];
            }
        }
        return result;
    }

    function onConvertTabs() {
        var textareas = document.querySelectorAll('textarea');
        if (!textareas) {
            console.log("textareas not found");
            return;
        }

        for (var index = 0; index < textareas.length; index++) {
            var textarea = textareas[index];

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
        //textarea.value = textarea.value.replace(/;/g, '\t');
        console.log("converted text to tabs");
    }

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

        // setTimeout(function() { tryAddConvertToTabs(); }, 1000);
    }

    function uploadForThing(thing) {
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
        customUploadButton.setAttribute('class', 'btn btn-mini');
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

    function clickAllDeleteButtons() {
        var deleteButtons = document.querySelectorAll('[title="Delete this audio file"]');
        for (var i = 0; i < deleteButtons.length; i++) {
            var deleteButton = deleteButtons[i];
            deleteButton.click();
        }
    }

    function clickAllAddAudioButtons() {
        var addAudioButtons = document.querySelectorAll('[title="AddAudio"]');
        for (var i = 0; i < addAudioButtons.length; i++) {
            var addAudioButton = addAudioButtons[i];
            addAudioButton.click();
        }
    }

    function findMissingAndAddUpload() {
        var things = document.getElementsByClassName('thing');
        for (var i = 0; i < things.length; i++) {

            if (i >= 9999) {
                break;
            }

            var thing = things[i];
            if (uploadForThing(thing)) {
                //break;
            }
        }
    }

    //setTimeout(function() { findAndUpload(); }, 5000);
    setTimeout(function() { addButtons(); }, 1000);
})();
