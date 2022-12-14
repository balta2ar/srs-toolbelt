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
    static fromString(s, title) {
        const root = new Node(title, [])
        var stack = [root]
        var lastIndent = 0
        function top() { return stack[stack.length-1] }
        function lastChild() { return top().children[top().children.length-1] }
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
        x: x, y: y, //style: 'fill: #ffffff;',
        class: 'label-text',
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
        x: rx, y: ry, width: rw, height: rh, rx: 5, ry: 5,
        class: 'label-rect',
        // style: 'fill: #486AFF; stroke: #000000; stroke-width: 0'
    })
    r.addEventListener('click', (e) => {
        selectLabel(r)
        console.log(`click: ${text}`)
    })
    parent.insertBefore(r, t)
    return [parent, r.getBoundingClientRect().width, h]
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
        const dx = width * zoom
        const dy = height * zoom
        x += dx * sign
        y += dy * sign
        width -= dx * 2 * sign
        height -= dy * 2 * sign
        x += zoom * width * (mousePosX - 0.5)
        y += zoom * height * (mousePosY - 0.5)
        if (delta < 0) {
            scale *= (1.0 + zoom)
        } else {
            scale /= (1.0 + zoom)
        }
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
    enableSvgViewboxMoveAndZoom(svg)
    trackMousePosition(svg)

    const root = example()
    console.log('root: %o', root)

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
    // layoutLeftCenteredTree(root, g4, 0, 0)
    // addClass(g4, 'rect', 'color4')

    // const g5 = addSvg(svg, 'g', { transform: 'translate(1250, 250)' })
    // layoutBothSidesCenteredTree(root, g5, 0, 0)
    // addClass(g5, 'rect', 'color5')

    const g6 = addSvg(svg, 'g', { transform: 'translate(10, 50)' })
    const norsk = Node.fromString(norskXmind, 'norsk')
    console.log('norsk: %o', norsk)
    // layoutRightCenteredTree(norsk, g6, 0, 0)
    layoutBothSidesCenteredTree(norsk, g6, 0, 0)
    addClass(g6, 'rect', 'color1')
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