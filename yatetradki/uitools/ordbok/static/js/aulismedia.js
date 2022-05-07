window.onload = function() {
    console.log("loaded")
}

function pageUrl(page) {
    return `/aulismedia/static/${page}`
}

function nextPage() {
    document.getElementById("imgdiv").src = pageUrl("nor0001.jpg");
}

function prevPage() {
    document.getElementById("imgdiv").src = pageUrl("nor0001.jpg");
}

