import json
import subprocess
import re
from collections import defaultdict, deque
from statistics import mean, median

d3_json="""<!DOCTYPE html>
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
    const nodes = <<node_part>>;

    const links = <<link_part>> ;

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


        
def get_task_dependencies_impl(command):
    try:
        # Run the command and capture its output
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        output = result.stdout
        
        # Extract the task_dep block
        match = re.search(r"task_dep\s+:\s+(.*?)(?:\n\n|\Z)", output, re.DOTALL)
        if match:
            task_dep_lines = match.group(1).strip().split("\n")
            # Clean and return the list of dependencies
            tasks = [line.strip(" -").strip() for line in task_dep_lines if line.strip()]
            return tasks
        else:
            print("No task_dep found in the output.")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")
        return []


def get_task_dependencies(task_label):
    
    # Command to run
    command = f"python3 /home/kabira/Development/cloudworks-monallabs/deployment-service/devel/test_drive.py info {task_label}"
    dependencies = get_task_dependencies_impl(command)
    return dependencies[:-1]


# Topological sort
def topological_sort(nodes, links):
    in_degree = defaultdict(int)
    adj_list = defaultdict(list)

    # Initialize in-degree and adjacency list
    for node in nodes:
        in_degree[node["id"]] = 0

    for link in links:
        adj_list[link["source"]].append(link["target"])
        in_degree[link["target"]] += 1

    # Kahn's algorithm
    queue = deque([node["id"] for node in nodes if in_degree[node["id"]] == 0])
    sorted_nodes = []

    while queue:
        current = queue.popleft()
        sorted_nodes.append(current)

        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return sorted_nodes


class task_graph_d3json:

    def __init__(self):
        self.nodes = []  # List of nodes
        self.links = []  # List of links
        self.node_map = {}  # Map to ensure unique nodes
        self.link_id = 1  # Unique ID for links
        self.width=2560
        self.height=1440
        self.quad_map = {}
    def add_node(self, task_label):
        """Add a node to the graph if it doesn't already exist."""
        if task_label not in self.node_map:
            node_id = len(self.nodes) + 1
            self.node_map[task_label] = node_id
            self.nodes.append({"id": node_id, "name": task_label})

    def add_link(self, source, target):
        """Add a link between two nodes."""
        self.links.append({
            "id": f"link-{self.link_id}",
            "source": self.node_map[source],
            "target": self.node_map[target],
            "label": f"{source} -> {target}"  # Label for the link
        })
        self.link_id += 1

    def build_task_graph(self, root_task):
        queue = [root_task]
        visited = set()

        while queue:
            current_task = queue.pop(0)
            if current_task in visited:
                continue
            visited.add(current_task)

            # Add the current task as a node
            self.add_node(current_task)

            # Get dependencies and add them to the graph
            dependencies = get_task_dependencies(current_task)
            for dep in dependencies:
                self.add_node(dep)
                self.add_link(current_task, dep)
                if dep not in visited:
                    queue.append(dep)



    def graph_json(self):
        # Output the graph in D3.js format
        d3_graph = {
            "nodes": self.nodes,
            "links": self.links
        }

        return json.dumps(d3_graph, indent=2)


        
    def topological_sort(self):
        in_degree = defaultdict(int)
        self.adj_list = defaultdict(list)
        self.rev_adj_list = defaultdict(list)

        # Initialize in-degree and adjacency list
        for node in self.nodes:
            in_degree[node["id"]] = 0

        for link in self.links:
            self.adj_list[link["source"]].append(link["target"])
            self.rev_adj_list[link["target"]].append(link["source"])
            in_degree[link["target"]] += 1

        # Kahn's algorithm
        queue = deque([[node["id"] for node in self.nodes if in_degree[node["id"]] == 0]])
        sorted_nodes = []
        curr_level = 0
        self.level_map = {}

        while queue:
            items = queue.popleft()
            zero_indeg_nodes = []
            for current in items:
                self.level_map[current] = curr_level
                sorted_nodes.append(current)
                for neighbor in self.adj_list[current]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        zero_indeg_nodes.append(neighbor)

            if len(zero_indeg_nodes) > 0:
                queue.append(zero_indeg_nodes)
            curr_level = curr_level + 1

        return sorted_nodes

    def postprocess(self):
        max_level = max(self.level_map.values())
        nodes_at_level = [[] for _ in range(max_level+1)]
        print("adj_list = ", self.adj_list)
        for node, level in self.level_map.items():
            nodes_at_level[level].append(node)

        root_id = nodes_at_level[0][0]
        root_quad = 0
        self.quad_map[root_id] = (0, ((-1 * self.height)/2, self.height/2)) 
        for i in range(1, len(nodes_at_level)):
            nodes =  nodes_at_level[i]
            # if there only a single node at this level
            if len(nodes) == 1:
                the_node = nodes[0]
                #quad_map of all the nodes 
                parents_quad_map = [self.quad_map[_] for _ in self.rev_adj_list[the_node]]
                # not dealing with diamond shape
                assert len(parents_quad_map) == 1
                self.quad_map[the_node] = parents_quad_map[0]
                print(f"quad for node {the_node} = ", self.quad_map[the_node])

            else:
                adj_list = defaultdict(list)
                for node in nodes:
                    assert len(self.rev_adj_list[node]) == 1
                    adj_list[self.rev_adj_list[node][0]].append(node)

                for parent, childs in adj_list.items():
                    assert parent in self.quad_map
                    parent_quad = self.quad_map[parent]
                    start, end = parent_quad[1]
                    
                    num_childs = len(childs)

                    span_width = end - start
                    band_width = span_width /num_childs
                    for idx, achild in enumerate(childs):
                        band_start_pos = start + idx * band_width
                        band_end_pos = band_start_pos + band_width
                        child_pos  = (band_start_pos + band_end_pos)/2
                        self.quad_map[achild] = (child_pos, (band_start_pos, band_end_pos))
                        print(f"quad for node {achild} = ", self.quad_map[achild])

    def assign_position(self):
        max_level = max(self.level_map.values())
        nodes_at_level = {level: [] for level in range(max_level + 1)}
        # Group nodes by level
        for node, level in self.level_map.items():
            nodes_at_level[level].append(node)

        #root to leaf is horizontal
        x_gap = self.width/max_level

        positions = {}
        for level in range(max_level):
            nodes = nodes_at_level[level]
            x_position = level * x_gap
            for i, node in enumerate(nodes):
                y_position = self.quad_map[node][0]
                positions[node] = {"x": x_position, "y": y_position}
                self.nodes[node]['x'] = x_position
                self.nodes[node]['y'] = y_position
                print(node, x_position, y_position)
        print(positions)

    def gen_d3_json(self):
        output =  re.sub("<<node_part>>", json.dumps( self.nodes, indent=2), d3_json)
        output = re.sub("<<link_part>>", json.dumps( self.links, indent=2), output)
        # Write JSON to file with proper formatting
        from bs4 import BeautifulSoup
        with open("output.html", "w") as f:
            soup = BeautifulSoup(output, "html.parser")
            f.write(soup.prettify())  # This will format and display the HTML

builder = task_graph_d3json()
root_task = "final"
builder.build_task_graph(root_task)
builder.topological_sort()
builder.postprocess()
# print(builder.level_map)
builder.assign_position()

builder.gen_d3_json()
