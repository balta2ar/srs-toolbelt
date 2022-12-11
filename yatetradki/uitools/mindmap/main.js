let main
window.onload = function () {
    main = document.getElementById('main')
    main.innerText = "init..."

    Main()
}

class Node {
    constructor(text, children) {
        this.id = 0
        this.text = text
        this.children = children
    }
}

function example() {
    return new Node("norsk", [
        new Node("liv omstendigheter", [
            new Node("familie", []),
            new Node("arbeid", []),
        ]),
        new Node("handlinger", [
            new Node("bevegelse", [
                new Node("gå", []),
                new Node("stå", []),
                new Node("pile ut", []),
            ]),
            new Node("slå / kamp", [
                new Node("dytte", []),
                new Node("skyve", []),
            ]),
        ]),
        new Node("følelser", [
            new Node("positive", [
                new Node("lykke", []),
                new Node("glede", []),
            ]),
            new Node("negative", [
                new Node("sorg", []),
                new Node("angst", []),
                new Node("sin", []),
            ]),
        ]),
    ])
}

function addLabel(parent, text, x, y) {
    const t = addSvg(parent, 'text', {
        x: x, y: y, style: 'fill: #ffffff;'
    })
    t.textContent = text
    const w = t.getComputedTextLength()
    const b = t.getBoundingClientRect()
    const xmargin = 6
    const ymargin = 6
    const yoff = b.height/2 + ymargin
    const r = makeSvg('rect', {
        x: x-xmargin, y: y-yoff, width: w+2*xmargin, height: b.height, //-ymargin
        style: 'fill: #486AFF; stroke: #000000; stroke-width: 0'
    })
    parent.insertBefore(r, t)
    return [w, b.height]
}

function layoutNaiveDownTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 30

    function scan(node, x, y) {
        const [w, h] = addLabel(parent, node.text, x, y)
        var childI = 0
        var maxR = x
        for (const child of node.children) {
            const mx = childI === 0 ? 0 : marginX
            const [l, r] = scan(child, maxR + mx, y + marginY)
            maxR = Math.max(maxR, r)
            childI++
        }
        return [x, Math.max(x + w, maxR)]
    }

    scan(root, baseX, baseY)
}

function layoutNaiveRightTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(node, x, y) {
        const [w, h] = addLabel(parent, node.text, x, y)
        var childI = 0
        var maxB = y
        for (const child of node.children) {
            const my = childI === 0 ? 0 : marginY
            const [t, b] = scan(child, x + w + marginX, maxB + my)
            maxB = Math.max(maxB, b)
            childI++
        }

        return [y, Math.max(y + marginY, maxB)]
    }

    scan(root, baseX, baseY)
}

function Main() {
    main.innerText = ""
    var svg = addSvg(main, 'svg', {
        width: "100%",
        height: "100%",
        style: 'border:1px solid #000000'
    })

    var g = addSvg(svg, 'g', {
        transform: 'translate(10, 20)'
    })

    var text = addSvg(g, 'text', {
        x: 0,
        y: 0,
        style: 'fill: #000000; stroke: #ff0000; stroke-width: 1'
    })

    text.textContent = 'hello'

    const root = example()
    console.log('root: %o', root)
    const g2 = addSvg(svg, 'g', {
        transform: 'translate(50, 100)'
    })
    layoutNaiveRightTree(root, g2, 0, 0)
    const g3 = addSvg(svg, 'g', {
        transform: 'translate(400, 100)'
    })
    layoutNaiveDownTree(root, g3, 0, 0)
}

function makeSvg(type, attr) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', type);
    forEach(attr, (k, v) => {
        el.setAttribute(k, v)
    })
    return el
}

function addSvg(parent, type, attr) {
    var el = makeSvg(type, attr)
    parent.appendChild(el)
    return el
}

function addElement(parent, type, attr) {
    var el = document.createElement(type);
    parent.appendChild(el)
    forEach(attr, (k, v) => {
        el.setAttribute(k, v)
    })
    return el
}

function forEach(obj, cb) {
    if (typeof obj != "object") {
        return
    }
    for (const k of Object.keys(obj)) {
        if (k) {
            cb(k, obj[k])
        }
    }
}
