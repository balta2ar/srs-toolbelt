window.onload = function() {
}

function OnFocusOut(that) {
    let nameIndex = that.id.split('/')
    let name = nameIndex[0]
    let index = nameIndex[1]
    console.log(`OnFocusOut: ${name} ${index} ${that.value}`);
    Change(name, index, that.value)
}

function Change(name, index, value) {
    let dummy = 'dummy'
    xhr(`/change?name=${name}&index=${index}&value=${value}`, dummy, null, null)
}

function xhr(url, req, ok, err) {
    let xhr = new XMLHttpRequest();
    xhr.onload = () => {
        if (xhr.responseText) {
            var res = JSON.parse(xhr.responseText)
            console.debug("answer: %o", res)
            if (ok) ok(res)
        } else { // empty
            console.debug("empty answer")
            if (ok) ok()
        }
    }
    xhr.onerror = () => {
        console.error("error: %o", xhr)
        err(xhr.statusText)
    }
    if (req !== null) {
        xhr.open("POST", url)
//        xhr.send(JSON.stringify(req))
    } else {
        xhr.open("GET", url)
        xhr.send()
    }
    console.debug("sent: %o", xhr)
}
