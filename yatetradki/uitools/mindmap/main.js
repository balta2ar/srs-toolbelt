let main
let mousePosX
let mousePosY
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

function addLabel(parent, text, x, y, direction) {
    // const g = addSvg(parent, 'g', {
    //     // transform: `translate(${x}, ${y})`
    // })
    const t = addSvg(parent, 'text', {
        x: x, y: y, style: 'fill: #ffffff;',
    })
    t.textContent = text
    const w = t.getComputedTextLength()
    const h = t.getBoundingClientRect().height
    const xmargin = 6
    const ymargin = 6
    const yoff = h/2 + ymargin
    var rx = x-xmargin
    const ry = y-yoff
    const rw = w+2*xmargin
    const rh = h
    if (direction === 'left') {
        t.setAttribute('text-anchor', 'end')
        rx -= rw - 2*xmargin
    }
    const r = makeSvg('rect', {
        x: rx, y: ry, width: rw, height: rh,
        style: 'fill: #486AFF; stroke: #000000; stroke-width: 0'
    })
    parent.insertBefore(r, t)
    return [parent, w, h]
}

function layoutNaiveDownTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 30

    function scan(node, x, y) {
        const [g, w, h] = addLabel(parent, node.text, x, y, 'right')
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
        const [g, w, h] = addLabel(parent, node.text, x, y, 'right')
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

function layoutRightCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(node, parent, x, y) {
        const g = addSvg(parent, 'g', {})
        const gHeader = addSvg(g, 'g', {})
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, 'right')
        var childI = 0
        var maxB = y
        const gChildren = addSvg(g, 'g', {})
        for (const child of node.children) {
            const my = childI === 0 ? 0 : marginY
            const [t, b] = scan(child, gChildren, x + w + marginX, maxB + my)
            maxB = Math.max(maxB, b)
            childI++
        }
        maxB = Math.max(y + marginY, maxB)
        if (node.children.length > 0) {
            const yoff = gChildren.getBBox().height / 2 - gHeader.getBBox().height / 2
            gHeader.setAttribute('transform', `translate(0, ${yoff})`)
        }

        return [y, maxB]
    }

    scan(root, parent, baseX, baseY)
}

function layoutLeftCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(node, parent, x, y) {
        const g = addSvg(parent, 'g', {})
        const gHeader = addSvg(g, 'g', {})
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, 'left')
        var childI = 0
        var maxB = y
        const gChildren = addSvg(g, 'g', {})
        for (const child of node.children) {
            const my = childI === 0 ? 0 : marginY
            const cx = x - w - marginX
            const cy = maxB + my
            const [t, b] = scan(child, gChildren, cx, cy)
            maxB = Math.max(maxB, b)
            childI++
        }
        maxB = Math.max(y + marginY, maxB)
        if (node.children.length > 0) {
            const yoff = gChildren.getBBox().height / 2 - gHeader.getBBox().height / 2
            gHeader.setAttribute('transform', `translate(0, ${yoff})`)
        }

        return [y, maxB]
    }

    scan(root, parent, baseX, baseY)
}

function layoutBothSidesCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(level, dir, node, parent, x, y) {
        const g = addSvg(parent, 'g', {})
        const gHeader = addSvg(g, 'g', {})
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, dir)
        function midChild() { return Math.floor(node.children.length / 2) }
        function getMy(childI) {
            const first = childI === 0
            if (level > 0) { return first ? 0 : marginY }
            const mid = childI === midChild()
            return (first || mid) ? 0 : marginY
        }
        function nextDir(childI) {
            if (level > 0) { return dir }
            return childI < midChild() ? 'right' : 'left'
        }
        function getCx(nDir) {
            switch (nDir) {
                case 'left': return x - w - marginX
                case 'right': return x + w + marginX
                default: throw new Error('bad dir')
            }
        }
        var childI = 0
        var maxB1 = y
        var maxB2 = y
        var lastNextDir = undefined
        const gChildrenR = addSvg(g, 'g', {})
        const gChildrenL = addSvg(g, 'g', {})
        for (const child of node.children) {
            const nDir = nextDir(childI)
            if (lastNextDir === undefined) { lastNextDir = nDir }
            if (lastNextDir !== nDir) { // reset maximums
                maxB2 = maxB1
                maxB1 = y
                lastNextDir = nDir
            }
            const my = getMy(childI) //childI === 0 ? 0 : marginY
            const cx = getCx(nDir)
            const cy = maxB1 + my
            const gChildren = childI < midChild() ? gChildrenR : gChildrenL
            const [t, b] = scan(level+1, nDir, child, gChildren, cx, cy)
            maxB1 = Math.max(maxB1, b)
            childI++
        }
        maxB1 = Math.max(y + marginY, maxB1, maxB2)
        function byBBoxHeight(a, b) {
            if (a.getBBox().height === b.getBBox().height) { return 0 }
            return a.getBBox().height < b.getBBox().height ? -1 : 1
        }
        if (node.children.length > 0) {
            const yoff = g.getBBox().height / 2 - gHeader.getBBox().height / 2
            gHeader.setAttribute('transform', `translate(0, ${yoff})`)
            if (level === 0 && node.children.length > 1) {
                const children = [gChildrenR, gChildrenL]
                children.sort(byBBoxHeight)
                children[0].setAttribute('transform', `translate(0, ${yoff-marginY})`)
            }
        }

        return [y, maxB1]
    }

    scan(0, 'right', root, parent, baseX, baseY)
}

// function enableMoveAndZoomViewport(el) {
//     var x = 0
//     var y = 0
//     var scale = 1
//     var dragging = false
//     var dragStartX = 0
//     var dragStartY = 0
//     el.addEventListener('mousedown', function (e) {
//         if (e.which !== 1) { return }
//         dragging = true
//         dragStartX = e.clientX
//         dragStartY = e.clientY
//     })
//     el.addEventListener('mousemove', function (e) {
//         if (dragging) {
//             const dx = e.clientX - dragStartX
//             const dy = e.clientY - dragStartY
//             x += dx
//             y += dy
//             dragStartX = e.clientX
//             dragStartY = e.clientY
//             el.setAttribute('transform', `translate(${x}, ${y}) scale(${scale})`)
//             console.log(`viewbox: %o`, el.viewBox)
//         }
//     })
//     el.addEventListener('mouseup', function (e) {
//         dragging = false
//     })
//     el.addEventListener('wheel', function (e) {
//         const delta = e.deltaY
//         const zoom = 1.05
//         if (delta < 0) {
//             scale *= zoom
//         } else {
//             scale /= zoom
//         }
//         el.setAttribute('transform', `translate(${x}, ${y}) scale(${scale})`)
//         console.log(`viewbox: %o`, el.viewBox)
//     })
// }

function enableSvgViewboxMoveAndZoom(svg) {
    var x = 0
    var y = 0
    var width = svg.getBoundingClientRect().width
    var height = svg.getBoundingClientRect().height
    console.log(`width: %o, height: %o`, width, height)
    var scale = 1
    var dragging = false
    var dragStartX = 0
    var dragStartY = 0
    svg.addEventListener('mousedown', function (e) {
        if (e.which !== 1) { return }
        e.preventDefault()
        dragging = true
        dragStartX = e.clientX
        dragStartY = e.clientY
    })
    svg.addEventListener('mousemove', function (e) {
        if (dragging) {
            e.preventDefault()
            const dx = e.clientX - dragStartX
            const dy = e.clientY - dragStartY
            x -= dx
            y -= dy
            dragStartX = e.clientX
            dragStartY = e.clientY
            svg.setAttribute('viewBox', `${x} ${y} ${width} ${height}`)
        }
    })
    svg.addEventListener('mouseup', function (e) {
        e.preventDefault()
        dragging = false
    })
    svg.addEventListener('wheel', function (e) {
        e.preventDefault()
        const delta = e.deltaY
        const zoom = 0.05 // delta < 0 ? 0.95 : 1.05
        const sign = delta < 0 ? 1 : -1
        const dx = width * zoom
        const dy = height * zoom
        x += dx * sign
        y += dy * sign
        width -= dx * 2 * sign
        height -= dy * 2 * sign
        x += zoom * width * (mousePosX - 0.5)
        y += zoom * height * (mousePosY - 0.5)
        // if (delta < 0) {
        //     scale *= zoom
        // } else {
        //     scale /= zoom
        // }
        svg.setAttribute('viewBox', `${x} ${y} ${width} ${height}`)
    })
}

function trackMousePosition(svg) {
    main.addEventListener('mousemove', function (e) {
        mousePosX = e.clientX / window.innerWidth
        mousePosY = e.clientY / window.innerHeight
    })
}

function Main() {
    main.innerText = ""
    var svg = addSvg(main, 'svg', {
        width: "100%",
        height: "100%",
        // style: 'border:1px solid #000000'
    })
    // enableMoveAndZoomViewport(svg)
    enableSvgViewboxMoveAndZoom(svg)
    trackMousePosition(svg)

    // var g = addSvg(svg, 'g', {
    //     transform: 'translate(10, 20)'
    // })

    // var text = addSvg(g, 'text', {
    //     x: 0,
    //     y: 0,
    //     style: 'fill: #000000; stroke: #ff0000; stroke-width: 1'
    // })
    // text.textContent = 'hello'

    const root = example()
    console.log('root: %o', root)
    const g1 = addSvg(svg, 'g', {
        transform: 'translate(10, 50)'
    })
    layoutNaiveRightTree(root, g1, 0, 0)
    restyle(g1, 'rect', 'fill: #486AFF; stroke: #000000; stroke-width: 0')

    const g3 = addSvg(svg, 'g', {
        transform: 'translate(400, 50)'
    })
    layoutNaiveDownTree(root, g3, 0, 0)
    restyle(g3, 'rect', 'fill: #B86AFF; stroke: #000000; stroke-width: 0')

    const g4 = addSvg(svg, 'g', {
        transform: 'translate(50, 400)'
    })
    layoutRightCenteredTree(root, g4, 0, 0)
    restyle(g4, 'rect', 'fill: #B86AAF; stroke: #000000; stroke-width: 0')

    const g5 = addSvg(svg, 'g', {
        transform: 'translate(850, 250)'
    })
    layoutLeftCenteredTree(root, g5, 0, 0)
    restyle(g5, 'rect', 'fill: #986A3F; stroke: #000000; stroke-width: 0')

    const g6 = addSvg(svg, 'g', {
        transform: 'translate(1250, 250)'
    })
    layoutBothSidesCenteredTree(root, g6, 0, 0)
    restyle(g6, 'rect', 'fill: #18BAFF; stroke: #000000; stroke-width: 0')
}

function restyle(parent, query, style) {
    const els = parent.querySelectorAll(query)
    for (const el of els) {
        el.setAttribute('style', style)
    }
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
