(() => {
    let url = 'http://localhost:7000/subtitles?url=' + window.location.href;
    console.log('Opening subtitles: ' + url);
    open(url);
})()
