
import json

d3_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>D3.js Directed Acyclic Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .node circle {
      fill: steelblue;
      stroke: #333;
      stroke-width: 1.5px;
    }

    .node text {
      font: 12px sans-serif;
      text-anchor: middle;
      fill: #333;
    }

    .link {
      fill: none;
      stroke: #ccc;
      stroke-width: 1.5px;
      marker-end: url(#arrowhead);
    }

    .tooltip {
      position: absolute;
      background: white;
      padding: 5px;
      border: 1px solid #ccc;
      border-radius: 5px;
      font-size: 12px;
      pointer-events: none;
      opacity: 0;
    }
  </style>
</head>
<body>
  <svg width="800" height="600"></svg>
  <script>
    // Define the nodes and links for the DAG
    const nodes = [
      { id: "root", name: "Root" },
      { id: "A", name: "Node A" },
      { id: "B", name: "Node B" },
      { id: "C", name: "Node C" },
      { id: "D", name: "Node D" },
      { id: "E", name: "Node E" }
    ];

    const links = [
      { source: "root", target: "A" },
      { source: "root", target: "B" },
      { source: "A", target: "C" },
      { source: "B", target: "D" },
      { source: "C", target: "E" },
      { source: "D", target: "E" }
    ];

    // Set up SVG and layout
    const svg = d3.select("svg");
    const width = +svg.attr("width");
    const height = +svg.attr("height");

    const g = svg.append("g").attr("transform", "translate(40, 40)");

    // Define arrowheads for links
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 10)
      .attr("refY", 0)
      .attr("markerWidth", 7)
      .attr("markerHeight", 7)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#ccc");

    // Create a simulation for the nodes and links
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter((width - 80) / 2, (height - 80) / 2))
      .force("y", d3.forceY(0).strength(0.1))
      .force("x", d3.forceX(0).strength(0.1));

    // Draw the links
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "link");

    // Draw the nodes
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node");

    node.append("circle")
      .attr("r", 8)
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded));

    node.append("text")
      .attr("dy", -12)
      .text(d => d.name);

    // Tooltip for node labels
    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip");

    node.on("mouseover", (event, d) => {
      tooltip.style("opacity", 1)
        .html(`<strong>${d.name}</strong>`)
        .style("left", (event.pageX + 5) + "px")
        .style("top", (event.pageY + 5) + "px");
    });

    node.on("mouseout", () => {
      tooltip.style("opacity", 0);
    });

    // Update positions on each tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Dragging behavior
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  </script>
</body>
</html>
"""

from bs4 import BeautifulSoup

soup = BeautifulSoup(d3_html, "html.parser")
print(soup.prettify())  # This will format and display the HTML


