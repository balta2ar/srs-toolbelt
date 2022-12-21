let main
let mouseRatioX
let mouseRatioY
window.onload = function () {
    main = document.getElementById('main')
    main.innerText = "init..."

    Main()
}

class Data {
    constructor(text, children) {
        this.text = text
        this.children = children
    }
    static fromString(s, title) {
        const root = new Node(title, [])
        var stack = [root]
        var lastIndent = 0
        function top() { return stack[stack.length - 1] }
        function lastChild() { return top().children[top().children.length - 1] }
        for (const line of s.split('\n')) {
            if (line.length === 0) { continue }
            const indent = line.match(/^\s*/)[0].length
            if (indent > lastIndent) {
                stack.push(lastChild())
                top().children.push(new Node(line.trim(), []))
            } else if (indent < lastIndent) {
                for (var _ = 0; _ < lastIndent - indent; _++) { stack.pop() }
                top().children.push(new Node(line.trim(), []))
            } else {
                top().children.push(new Node(line.trim(), []))
            }
            lastIndent = indent
        }
        return root
    }
}

class Svg {
    static fromData(svg, data, x, y, layoutFn, colorKlass) {
        const tree = addSvg(svg, 'g', { transform: `translate(${x}, ${y})` })
        // layoutLeftCenteredTree(data, tree, 0, 0)
        layoutFn(data, tree, 0, 0)
        // addClass(tree, 'rect', 'color4')
        addClass(tree, 'rect', `${colorKlass}-rect`)
        addClass(tree, 'path', `${colorKlass}-path`)
        return tree
    }
}

function test1() {
    const data = new Data()
    // const g1 = Svg.fromData(data)
}

function exampleData() {
    return new Data("norsk", [
        new Data("liv omstendigheter", [
            new Data("familie", []),
            new Data("arbeid", []),
        ]),
        new Data("handlinger", [
            new Data("bevegelse", [
                new Data("gå", []),
                new Data("stå", []),
                new Data("pile ut", []),
            ]),
            new Data("slå / kamp", [
                new Data("dytte", []),
                new Data("skyve", []),
            ]),
        ]),
        new Data("følelser", [
            new Data("positive", [
                new Data("lykke", []),
                new Data("glede", []),
            ]),
            new Data("negative", [
                new Data("sorg", []),
                new Data("angst", []),
                new Data("sin", []),
            ]),
        ]),
        new Data("merke / flekk", [
            new Data("strekk", []),
            new Data("pigg", []),
            new Data("ripe", []),
            new Data("volley", []),
        ]),
        new Data("egenskap", [
            new Data("fæl", []),
            new Data("vindskjev / skeiv", []),
            new Data("tilbakestående", []),
            new Data("lurvet", []),
        ]),
    ])
}

// 0 -- 0..90º, 1 -- 90..180º, 2 -- 180..270º, 3 -- 270..360º
function section2quarter(x1, y1, x2, y2) {
    if (x1 <= x2) {
        if (y1 <= y2) { return 3 }
        else { return 0 }
    } else {
        if (y1 <= y2) { return 2 }
        else { return 1 }
    }
}

function addHorizontalPath(parent, x1, y1, x2, y2) {
    const x = Math.min(x1, x2)
    const y = Math.min(y1, y2)
    const g = addSvg(parent, 'g', {})
    g.setAttribute('transform', `translate(${x}, ${y})`)
    const d = genVerticalPath(x1, y1, x2, y2)
    // console.log(`d: ${d}`)
    addSvg(g, 'path', {class: 'path', d: d})
}

function genVerticalPath(x1, y1, x2, y2) {
    const [midX, midY] = [(x1 + x2) / 2, (y1 + y2) / 2]
    const [w, h] = [Math.abs(x2 - x1), Math.abs(y2 - y1)]
    const [hw, hh] = [w / 2, h / 2]
    const [x, y] = [Math.min(x1, x2), Math.min(y1, y2)]
    const quarter = section2quarter(x1, y1, x2, y2)
    const r = Math.min(5, h)
    const p = (x) => Math.max(0, x)
    if (quarter === 0) { // move to top-right
        if (y1 == y2) return `M 0 0 l ${w} 0`
        return `M 0 ${h} l ${p(hw-r)} 0
                a ${r} ${r} 0 0 0 ${r} -${r}
                l 0 -${p(h-2*r)}
                a ${r} ${r} 0 0 1 ${r} -${r}
                l ${p(hw-r)} 0
        `
    } else if (quarter === 1) { // move to top-left
        if (y1 == y2) return `M ${w} 0 l -${w} 0`
        return `M ${w} ${h} l -${p(hw-r)} 0
                a ${r} ${r} 0 0 1 -${r} -${r}
                l 0 -${p(h-2*r)}
                a ${r} ${r} 0 0 0 -${r} -${r}
                l -${p(hw-r)} 0
        `
    } else if (quarter === 2) { // move to bottom-left
        if (y1 == y2) return `M ${w} 0 l -${w} 0`
        return `M ${w} 0 l -${p(hw-r)} 0
                a ${r} ${r} 0 0 0 -${r} ${r}
                l 0 ${p(h-2*r)}
                a ${r} ${r} 0 0 1 -${r} ${r}
                l -${p(hw-r)} 0
        `
    } else if (quarter === 3) { // move to bottom-right
        if (y1 == y2) return `M 0 0 l ${w} 0`
        return `M 0 0 l ${p(hw-r)} 0
                a ${r} ${r} 0 0 1 ${r} ${r}
                l 0 ${p(h-2*r)}
                a ${r} ${r} 0 0 0 ${r} ${r}
                l ${p(hw-r)} 0
        `
    }
}

function addLabel(parent, text, x, y, dir) {
    // const g = addSvg(parent, 'g', {
    //     // transform: `translate(${x}, ${y})`
    // })
    const t = addSvg(parent, 'text', {
        x: x, y: y, //style: 'fill: #ffffff;',
        class: 'label-text',
    })
    t.textContent = text
    const w = t.getComputedTextLength()
    const h = t.getBoundingClientRect().height
    const xmargin = 6
    const ymargin = 6
    const yoff = h / 2 + ymargin
    var rx = x - xmargin
    const ry = y - yoff
    const rw = w + 2 * xmargin
    const rh = h
    if (dir === 'left') {
        t.setAttribute('text-anchor', 'end')
        rx -= rw - 2 * xmargin
    }
    const r = makeSvg('rect', {
        x: rx, y: ry, width: rw, height: rh, rx: 5, ry: 5,
        class: 'label-rect',
        // style: 'fill: #486AFF; stroke: #000000; stroke-width: 0'
    })
    r.addEventListener('click', (e) => {
        selectLabel(r)
        console.log(`click: ${text}`)
    })
    parent.insertBefore(r, t)
    return [parent, r.getBoundingClientRect().width, r.getBoundingClientRect().height]
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

    function scan(node, parent, x, y) {
        const g = contChild(parent)
        const gHeader = contHeader(g)
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, 'right')
        var childI = 0
        var maxB = y
        const gChildren = contChildren(g)
        for (const child of node.children) {
            const my = childI === 0 ? 0 : marginY
            const cx = x + w + marginX
            const cy = maxB + my
            const [t, b] = scan(child, gChildren, cx, cy)
            maxB = Math.max(maxB, b)
            childI++
        }
        for (const gChild of gChildren.children) {
            const cx = x + w + marginX
            const cy = gChild.firstChild.getBoundingClientRect().y
            const hy = gHeader.getBoundingClientRect().y
            const yChildOff = hy - cy
            addHorizontalPath(g, x+w-marginX/2, y-marginY/2, cx, y-marginY/2-yChildOff)
        }
        return [y, Math.max(y + marginY, maxB)]
    }
    scan(root, parent, baseX, baseY)
}

function contChild(parent) { return addSvg(parent, 'g', {class: 'g-child'}) }
function contHeader(parent) { return addSvg(parent, 'g', {class: 'g-header'}) }
function contChildren(parent) { return addSvg(parent, 'g', {class: 'g-children'}) }

function layoutRightCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(node, parent, x, y) {
        const g = contChild(parent)
        const gHeader = contHeader(g)
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, 'right')
        var childI = 0
        var maxB = y
        const gChildren = contChildren(g)
        for (const child of node.children) {
            const my = childI === 0 ? 0 : marginY
            const [t, b] = scan(child, gChildren, x + w + marginX, maxB + my)
            maxB = Math.max(maxB, b)
            childI++
        }
        maxB = Math.max(y + marginY, maxB)
        var yHeaderOff = 0
        if (node.children.length > 0) {
            yHeaderOff = gChildren.getBBox().height / 2 - gHeader.getBBox().height / 2
            gHeader.setAttribute('transform', `translate(0, ${yHeaderOff})`)
        }
        for (const gChild of gChildren.children) {
            const hy = gHeader.getBoundingClientRect().y
            const cy = gChild.firstChild.getBoundingClientRect().y
            const yChildOff = hy - cy
            const yFrom = y+yHeaderOff-h/4
            addHorizontalPath(g, x+w-marginX/2, yFrom, x+w+marginX, yFrom-yChildOff)
        }
        return [y, maxB]
    }

    scan(root, parent, baseX, baseY)
}

function layoutLeftCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(level, node, parent, x, y) {
        const g = contChild(parent)
        const gHeader = contHeader(g)
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, 'left')
        var maxB = y
        const gChildren = contChildren(g)
        for (const [childI, child] of node.children.entries()) {
            const my = childI === 0 ? 0 : marginY
            const cx = x-w-marginX
            const cy = maxB+my
            const [t, b] = scan(level+1, child, gChildren, cx, cy)
            maxB = Math.max(maxB, b)
        }
        maxB = Math.max(y + marginY, maxB)
        var yHeaderOff = 0
        if (node.children.length > 0) {
            yHeaderOff = gChildren.getBBox().height/2 - gHeader.getBBox().height/2
            gHeader.setAttribute('transform', `translate(0, ${yHeaderOff})`)
        }
        for (const gChild of gChildren.children) {
            const hy = gHeader.getBoundingClientRect().y
            const cy = gChild.firstChild.getBoundingClientRect().y
            const yChildOff = hy - cy
            const yFrom = y+yHeaderOff-h/4
            addHorizontalPath(g, x-w+marginX/2, yFrom, x-w-marginX, yFrom-yChildOff)
        }
        return [y, maxB]
    }

    scan(0, root, parent, baseX, baseY)
}

function layoutBothSidesCenteredTree(root, parent, baseX, baseY) {
    const marginX = 20
    const marginY = 15

    function scan(level, dir, node, parent, x, y) {
        const g = contChild(parent)
        const gHeader = contHeader(g)
        const [_g, w, h] = addLabel(gHeader, node.text, x, y, dir)
        function mid() { return Math.floor(node.children.length / 2) }
        function getMy(childI) {
            const first = childI === 0
            return first ? 0 : marginY
        }
        function level0(a, b) { return (level===0) ? a : b }
        function getCx(nDir) {
            switch (nDir) {
                case 'left': return level0(x-2*marginX, x-w-marginX)
                case 'right': return x+w+marginX
                default: throw new Error('bad dir')
            }
        }
        var maxB = y
        function left() { return node.children.slice(0, mid()) }
        function right() { return node.children.slice(mid()) }
        function kids(children, dir, gChildren) {
            var maxBLocal = y
            for (const [childI, child] of children.entries()) {
                const my = getMy(childI)
                const cx = getCx(dir)
                const cy = maxBLocal + my
                const [t, b] = scan(level+1, dir, child, gChildren, cx, cy)
                maxBLocal = Math.max(maxBLocal, b)
            }
            maxB = Math.max(maxB, maxBLocal)
        }
        function getYOff() { return g.getBBox().height/2 - gHeader.getBBox().height/2 }
        function adjustHeader() {
            if (node.children.length > 0) {
                gHeader.setAttribute('transform', `translate(0, ${getYOff()})`)
            }
        }
        function byBBoxHeight(a, b) {
            if (a.getBBox().height === b.getBBox().height) { return 0 }
            return a.getBBox().height < b.getBBox().height ? -1 : 1
        }
        function adjustSmallestHalf(l, r) {
            if (node.children.length > 1) {
                const children = [l, r]
                children.sort(byBBoxHeight)
                const h0 = children[0].getBoundingClientRect().height
                children[0].setAttribute('transform', `translate(0, ${getYOff()-h0/4-marginY})`)
            }
        }
        function paths(gChildren, dir) {
            function xFrom() {
                if (dir === 'left') { return level0(x, x-w+marginX/2) }
                if (dir === 'right') { return x+w-marginX/2 }
                throw new Error('bad dir')
            }
            function xTo() {
                if (dir === 'left') { return xFrom()-level0(marginX*2, marginX*3/2) }
                if (dir === 'right') { return xFrom()+marginX*3/2 }
                throw new Error('bad dir')
            }
            for (const gChild of gChildren.children) {
                const hy = gHeader.getBoundingClientRect().y
                const cy = gChild.firstChild.getBoundingClientRect().y
                const yChildOff = hy - cy
                const yFrom = y+getYOff()-h/4
                addHorizontalPath(g, xFrom(), yFrom, xTo(), yFrom-yChildOff)
            }
        }
        if (level === 0) {
            const gChildrenR = contChildren(g)
            const gChildrenL = contChildren(g)
            kids(right(), 'right', gChildrenR)
            kids(left(), 'left', gChildrenL)
            adjustHeader()
            adjustSmallestHalf(gChildrenL, gChildrenR)
            paths(gChildrenR, 'right')
            paths(gChildrenL, 'left')
        } else {
            const gChildren = contChildren(g)
            kids(node.children, dir, gChildren)
            adjustHeader()
            paths(gChildren, dir)
        }
        maxB = Math.max(y + marginY, maxB)
        return [y, maxB]
    }
    scan(0, 'right', root, parent, baseX, baseY)
}

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
            x -= dx / scale
            y -= dy / scale
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
        var zoom1 = 1.0 - zoom * sign
        if (delta < 0) {
            scale *= (1.0 + zoom)
        } else {
            scale /= (1.0 + zoom)
        }
        const mouseVirtualX = x + mouseRatioX * width
        const newWidth = width * zoom1
        const newX = mouseVirtualX - mouseRatioX * newWidth
        const mouseVirtualY = y + mouseRatioY * height
        const newHeight = height * zoom1
        const newY = mouseVirtualY - mouseRatioY * newHeight
        x = newX
        y = newY
        width = newWidth
        height = newHeight

        svg.setAttribute('viewBox', `${x} ${y} ${width} ${height}`)
    })
}

function pageWidth() {
    return Math.max(
        document.body.scrollWidth,
        document.documentElement.scrollWidth,
        document.body.offsetWidth,
        document.documentElement.offsetWidth,
        document.documentElement.clientWidth,
        window.innerWidth
    );
}

function pageHeight() {
    return Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.offsetHeight,
        document.documentElement.clientHeight,
        window.innerHeight
    );
}

function trackMousePosition(svg) {
    main.addEventListener('mousemove', function (e) {
        mouseRatioX = e.clientX / pageWidth();
        mouseRatioY = e.clientY / pageHeight();
    })
}

function trackKeyboard() {
    document.addEventListener('keydown', function (e) {
        console.log(`document key: %o`, e.key)
        if (e.key === 'Escape') {
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault()
        } else if (e.key === 'ArrowRight') {
            e.preventDefault()
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
        } else if (e.key === 'ArrowDown') {
            e.preventDefault()
        } else if (e.key === 'Enter') {
            e.preventDefault()
        } else if (e.key === 'Tab') {
            e.preventDefault()
        } else if (e.key === 'Backspace') {
            e.preventDefault()
        }
    })
}

function Main() {
    main.innerText = ""
    var svg = addSvg(main, 'svg', {
        width: "100%",
        height: "100%",
        // style: 'border:1px solid #000000'
    })
    // cursor = #96DEFF
    // selected = #2EBDFF
    // blue line = #486AFF
    svg.innerHTML = `
    <defs>
    <radialGradient id="labelRectHoverGradient">
      <stop offset="0%" stop-color="white" stop-opacity="100%" />
      <stop offset="90%" stop-color="white" stop-opacity="100%" />
      <stop offset="100%" stop-color="#96DEFF"  stop-opacity="100%" />
    </radialGradient>
  </defs>
`
    enableSvgViewboxMoveAndZoom(svg)
    trackMousePosition(svg)
    trackKeyboard()

    const data = exampleData()
    console.log('root: %o', data)

    // const g1 = addSvg(svg, 'g', { transform: 'translate(10, 50)' })
    // layoutNaiveRightTree(root, g1, 0, 0)
    // addClass(g1, 'rect', 'color1')

    // const g2 = addSvg(svg, 'g', { transform: 'translate(400, 50)' })
    // layoutNaiveDownTree(root, g2, 0, 0)
    // addClass(g2, 'rect', 'color2')

    // const g3 = addSvg(svg, 'g', { transform: 'translate(50, 400)' })
    // layoutRightCenteredTree(root, g3, 0, 0)
    // addClass(g3, 'rect', 'color3')

    // const g4 = addSvg(svg, 'g', { transform: 'translate(850, 250)' })
    // layoutLeftCenteredTree(data, g4, 0, 0)
    // addClass(g4, 'rect', 'color4')
    
    const g1 = Svg.fromData(svg, data, 10, 50, layoutNaiveRightTree, 'color1')
    const g2 = Svg.fromData(svg, data, 400, 50, layoutNaiveDownTree, 'color2')
    const g3 = Svg.fromData(svg, data, 50, 700, layoutRightCenteredTree, 'color3')
    const g4 = Svg.fromData(svg, data, 850, 300, layoutLeftCenteredTree, 'color4')
    const g5 = Svg.fromData(svg, data, 1200, 180, layoutBothSidesCenteredTree, 'color5')
    
    // addVerticalPath(svg, 200, 500, 100, 100) // 1
    // addVerticalPath(svg, 400, 100, 300, 500) // 2
    // addVerticalPath(svg, 700, 500, 800, 100) // 0
    // addVerticalPath(svg, 900, 100, 1000, 500) // 3

    // const g5 = addSvg(svg, 'g', { transform: 'translate(1250, 250)' })
    // layoutBothSidesCenteredTree(root, g5, 0, 0)
    // addClass(g5, 'rect', 'color5')

    // const g6 = addSvg(svg, 'g', { transform: 'translate(10, 50)' })
    // const norsk = Node.fromString(norskXmind, 'norsk')
    // console.log('norsk: %o', norsk)
    // // layoutRightCenteredTree(norsk, g6, 0, 0)
    // layoutBothSidesCenteredTree(norsk, g6, 0, 0)
    // addClass(g6, 'rect', 'color1')
}

function restyle(parent, query, style) {
    const els = parent.querySelectorAll(query)
    for (const el of els) {
        el.setAttribute('style', style)
    }
}

function addClass(parent, query, klass) {
    const els = parent.querySelectorAll(query)
    for (const el of els) {
        //el.setAttribute('class', klass)
        el.classList.add(klass)
    }
}

function selectLabel(el) {
    const klass = 'label-selected'
    for (const old of document.querySelectorAll('.' + klass)) {
        old.classList.remove(klass)
    }
    el.classList.add(klass)
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

const norskXmind = `
verbs

adjektiver
	følelse
		trist
			vemodig

været

med andre gjenstander
	bevege
		riste
	ødelegge
		rive
		røste opp

bevegelse
	pile ut

våpen
	ruste opp

hjem
	soverom
		en seng
			laken
				vaske
			dyne
			ei pute
	kjøkken
		oppvaskmaskin
	stua

helse
	ulykke
		hånda i et fatle

gruppe ved
	ordklass
	handling
	kapittel
	sted/plass

job
	dokumenter
		refusjon
			bilag
				kvittering

b2
	k6 klima og miljø
		k6.5 Frederic Hauge
			ord
				fram til i dag
				avdekket områder
				han tilbakeviser dette
				gravd ned tønner med giftig avfall
				grave opp
				fastslå statens tinsyn
	k7 helsa vår
		k7.1 innledning
			ord
				minner om formynderstat
				ta opp spørsmål
				de er med på å påvirke den
				røykere må stille bakerst
				reklame for alkohol
		k7.3 taper mot bakterier
			ord
				bakterier haler innpå
				forekomsten av resistent bakterie
				forkorte sykdommen
				forkjølelse går over av seg selv
				kan til tider være
				fører til plager som allergi
				øynene renner
				har uttalt seg om dette til NRK
				noen løfter på øyenbrynene
				allergien er på sitt verste
				smogen ligger Oslo-gryta
		k7.4 psykisk helse
			ord
				hun bryter sammen
					nervous breakdown / collapse
				vegre seg
					hestitate / nøle
				innlang på avdelingen
				hvitt hefte
				håndskrift
					handwriting
				forlegen
					flau
				uttæret
					sliten
				beklage seg
					klage, complain
				smerte
				tilgi selv
					forgive yourself
				oppførsel
					væremåte
			ideer
		k7.5 Profilen Katti Anker Møller
			ord
				modig og kontroversiell person
				preget av frykt for nye graviditeter
				gjøre til ære for min bror
				gifte seg med en godseier
				fattige, ugifte mødre sto overfor problemer
					å ha krav på økonomisk hjelp
					hjemme for enslige mødre
						gjøre noe med det
						ble straks fullt
				arbeide sammen med svoger
					for å få loven vedtatt
						vakte protester
					født utenfor ekteskap
					rett til farens arv
					få tilgang til prevensjonsmidler
					stor interesse for saken
					ga seksuallopplysning
					få endret loven
					måtte søke en nemnd
	k8 litt norsk historie
		k8.1 innledning
			ord
				vi kjenner til hva som kjedde
				lykkelig er det folk
				unionsoppløsning
				en gravhaug på Oseberg
				innholde to kvinnelik
				en vakkert utskåret vogn
				datidas syn på døden

prøve

mine feil
	noe/noen
	bege dele/to
	skulle/ville/hadde
	det spørs om jeg rekker det eller ikke

preso
	fengsel
		i drift (in use)
		straff
			varetekt
			ubetinget fengselsstraf
			forvaring
			frihetsberøvelse
			innskrenkning
		kriminalomsorgen
			utøver makt
			innsyn
		rom
			køyeseng
			kjøkkenkrok
			gitter (bars) på vinduer
		isolasjon
			kjennelse fra domstolen
			fatte et vedtak om isolasjon
			mest nedverdigende
			ble løslatt
			vanlig soning
			et rom med mange til stede
			erverve erfaring
`