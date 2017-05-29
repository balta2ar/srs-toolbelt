// ==UserScript==
// @name         Upload audio to Memrise
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Automatically finds words without audios in memrise course and uploads the audio
// @author       balta2ar
// @match        https://www.memrise.com/course/1344980/baltazar-korean-words/edit/*
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

    function showError(response) {
        var msg = "An error occurred." +
            "\nresponseText: " + response.responseText +
            "\nreadyState: " + response.readyState +
            "\nresponseHeaders: " + response.responseHeaders +
            "\nstatus: " + response.status +
            "\nstatusText: " + response.statusText +
            "\nfinalUrl: " + response.finalUrl;
        console.log(msg);
    }

    function callAjax(url, callback){
        //alert("START");

        GM_xmlhttpRequest({
            method: "GET",
            url: url,
            synchronous: true,
            onload: function(response) {
                //alert('RECEIVED' + response.responseText);
                callback(JSON.parse(response.responseText));
            },
            onerror: function(response) {
                showError(response);
            },
        });
        //alert("END");
    }

    function getAudioForWord(word, onsuccess) {
        callAjax("http://localhost:5000/api/get_audio/" + encodeURIComponent(word), onsuccess);
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

        //alert('DISPLAY: ' + result);

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
                //alert('UPLOAD RESULT:' + response.responseText);
                onsuccess(response.responseText);
            },
            onerror: function(response) {
                showError(response);
            },
        };

        //var params = {
        //    thing_id: "query",
        //    cell_id: "3",
        //    cell_type: "column",
        //    csrfmiddlewaretoken: MEMRIZE.csrftoken,
        //};

        query.data = new FormData();
        for (var p in uploadFormParams) {
            query.data.append(p, uploadFormParams[p]);
        }

        //var formData = new FormData();
        var blob = resultToBlob(result);
        query.data.append('f', blob, 'sound.mp3');
        //formData.append('f', blob, 'sound.mp3');

        //query.headers = {"Content-Type": "multipart/form-data"};

        console.log(query);
        GM_xmlhttpRequest(query);

        //alert('DISPLAY DONE');
    }

    function onUploadedSuccessfully(result, thing, buttons) {
        buttons.innerHTML = 'UPLOADED';
        //alert(result);
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

    function addStartButton() {
        var header = document.querySelector('ul.header-nav');
        // <li class="header-nav-item plain ">
        // <a href="/home/" class="nav-item-btn">
        //            <span class="nav-item-btn-text">Home</span>
        var startButton = document.createElement('li');
        startButton.setAttribute('class', 'header-nav-item plain');
        //startButton.innerHTML = 'Add missing audio [bz]';
        startButton.innerHTML = '<a class="nav-item-btn"> <span class="nav-item-btn-text">Add missing audio</span> </a>';
        startButton.addEventListener('click', function(event) { findMissingAndUpload(); } );
        header.appendChild(startButton);
    }

    function uploadForThing(thing) {
        var buttons = thing.querySelector('button.btn.btn-mini.dropdown-toggle.disabled');

        if (buttons === null) {
            return false;
        }

        var buttonGroup = buttons.parentNode;

        var firstElement = buttons.parentNode.parentNode.parentNode.getElementsByClassName('text')[0];
        var word = firstElement.innerText.trim();
        var thingId = thing.getAttribute('data-thing-id');

        var uploadFormParams = {
            thing_id: thingId,
            cell_id: "3",
            cell_type: "column",
            csrfmiddlewaretoken: MEMRISE.csrftoken,
        };

        var customUploadButton = document.createElement('div');
        //<div class="btn btn-mini open-recorder">Record</div>
        customUploadButton.setAttribute('class', 'btn btn-mini');
        //customUploadButton.setAttribute('onclick', 'onAddAudio(' + word + ')');
        customUploadButton.addEventListener('click', function(event) {
            onAddAudio(word, uploadFormParams, thing, buttons);
        });
        onAddAudio(word, uploadFormParams, thing, buttons);
        customUploadButton.innerHTML = 'ADDAUDIO';

        buttonGroup.appendChild(customUploadButton);

        //var upload = buttons.parentNode.children[0]

        //var first = buttons;
        //var row = first.parentElement.parentElement.parentElement;
        //var word = row.children[1].innerText.trim();

        //callAjax("http://localhost:5000/api/get_audio/" + encodeURIComponent(word), displayResult);

        //alert(word);
        return true;
    }

    function findMissingAndUpload() {
        //alert("HELLO");
        //var things = document.querySelector('tbody', 'things');

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
    setTimeout(function() { addStartButton(); }, 1000);
})();
