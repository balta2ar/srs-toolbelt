(function() {
    'use strict';

    /*
     * Translate GM_xmlhttpRequest arguments into jQuery ajax call.
     * This file is used in memrise_syncher to inject memrise_client.js into
     * the PhantomJS page.
     */
    window.GM_xmlhttpRequest = function(query) {
        var new_query = {
            type:        query.method,
            url:         query.url,
            //dataType:   'JSON',
            headers:     query.headers,
            data:        query.data,
            processData: false,
            contentType: false,
            async:       false,
            //contentType: 'multipart/form-data',
            success:     function(response) {
                response.responseText = JSON.stringify(response)
                query.onload(response);
            },
            error:       function(response) {
                response.responseText = JSON.stringify(response)
                query.onerror(response);
            },
        };

        $.ajax(new_query);
    }

})();