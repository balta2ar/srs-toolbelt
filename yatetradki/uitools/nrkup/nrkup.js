(() => {
    function send(url) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://localhost:7000/download');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({
            'url': url,
        }));
    }
    let url = window.location.href;
    console.log('Sending: ' + url);
    send(url);
})()
