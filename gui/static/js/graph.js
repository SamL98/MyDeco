var w = window.innerWidth,
    h = window.innerHeight,
    block_w = 200,
    block_h = 100,
    block_spacing = block_h / 2,
    cfg_w = 0,
    cfg_h = 0

function translateTransform(x, y) {
    return 'translate(' + x + ', ' + y + ')'
}

function positionNode(node) {
    node.x = w / 2 - block_w / 2
    node.y = node.depth * (block_h + block_spacing)

    cfg_w = Math.max(cfg_w, node.x + block_w)
    cfg_h = Math.max(node.y + block_h)
}

function drawNode(container, node) {
    positionNode(node)
    console.log(node.start, node.depth)

    var g = container.append('g')
                      .attr('class', 'basic-block-container')
                      .attr('transform', translateTransform(node.x, node.y))

    g.append('rect')
     .attr('class', 'basic-block-rect')
     .attr('rx', 10)
     .attr('ry', 10)
     .style('width', block_w)
     .style('height', block_h)

    g.append('text')
     .attr('x', 10)
     .attr('y', 20)
     .text(node.start)
}

function drawEdges(container, node) {
}

function DFS(start, nodes, preFn = null, postFn = null) {
    start.depth = 0

    var buff    = [{node: start, par: null}],
        visited = []

    while (buff.length > 0) {
        var item = buff.shift(),
            node = item.node

        if (postFn !== null && node.par !== null)
            postFn(node.par)

        visited.push(node.start)

        if (preFn !== null)
            preFn(node)

        var prevLen = buff.length

        node.successors.forEach((succ, i) => {
            var succ_item = {
                node: nodes[succ],
                par: null
            }

            if (visited.indexOf(succ_item.node.start) >= 0)
                return

            succ_item.node.depth = node.depth + 1

            if (i == node.successors.length - 1)
                succ_item.par = node

            buff.unshift(succ_item)
        })
    }
}

function displayCFG(cfgJson) {
    var container = d3.select('#cfg-container')

    var preFn = (node) => drawNode(container, node),
        postFn = (node) => drawEdges(container, node)

    DFS(cfgJson.blocks[cfgJson.entry], 
        cfgJson.blocks,
        preFn,
        postFn)

    container.attr('width', cfg_w)
             .attr('height', cfg_h)
}
