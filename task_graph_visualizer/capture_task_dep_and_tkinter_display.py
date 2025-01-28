import json
import subprocess
import re
from collections import defaultdict, deque
from statistics import mean, median
import tkinter as tk
from idlelib.tooltip import Hovertip
import pickle

        
def get_task_dependencies_impl(command):
    try:
        # Run the command and capture its output
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        output = result.stdout
        print(output)
        # Extract the task_dep block
        match = re.search(r"task_dep\s+:\s+(.*?)(?:\n\n|\Z)", output, re.DOTALL)
        #match = re.search(r"task_dep\s*:\s*(?:\[(.*?)\]|(?:\n\s*-.*)+)", output, re.DOTALL)
        print(match)
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
    #command = f"python3 /home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/unit_tests/test_remote_task_with_target.py info {task_label}"
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
            node_id = len(self.nodes) 
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



    def pickle_graph(self, file_target):
        """Serialize the graph data structures to a file."""
        data = {
            "node_map": self.node_map,
            "nodes": self.nodes,
            "links": self.links
        }
        with open(file_target, 'wb') as file:
            pickle.dump(data, file)
        print(f"Graph successfully pickled to {file_target}.")

    def unpickle_graph(self, file_target):
        """Deserialize the graph data structures from a file."""
        with open(file_target, 'rb') as file:
            data = pickle.load(file)
            self.node_map = data["node_map"]
            self.nodes = data["nodes"]
            self.links = data["links"]
        print(f"Graph successfully unpickled from {file_target}.")

        
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
        print("nodes = ", self.nodes)
        max_level = max(self.level_map.values())
        nodes_at_level = [[] for _ in range(max_level+1)]
        for node, level in self.level_map.items():
            nodes_at_level[level].append(node)

        assert len(nodes_at_level[0]) == 1
        root_id = nodes_at_level[0][0]
        print("root node  = ", self.nodes[root_id]['name'])
        root_quad = 0
        self.quad_map[root_id] = (self.height/2, (0, self.height)) 
        for i in range(1, len(nodes_at_level)):
            nodes =  nodes_at_level[i]
            # if there only a single node at this level
            if len(nodes) == 1:
                the_node = nodes[0]
                #quad_map of all the nodes 
                parents_quad_map = [self.quad_map[_] for _ in self.rev_adj_list[the_node]]
                # not dealing with diamond shape
                #assert len(parents_quad_map) == 1
                # for now choose the zero parent
                self.quad_map[the_node] = parents_quad_map[0]

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
                        

    def assign_position(self):
        max_level = max(self.level_map.values()) + 1
        nodes_at_level = {level: [] for level in range(max_level)}
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

    def draw_nodes(self, canvas):
        color_map = {'bootstrap_computenode': 'red',
                     'setup_remote': 'blue'

            }
        for node in self.nodes:
            if 'x' in node:
                x = node['x']
                y = node['y']
                r = 15

                # Create a button in the center of the circle to hold the tooltip
                # Add text to the node and rotate it by 90 degrees
                full_label = node['name']
                parts = full_label.split(":")
                display_label = full_label
                tool_tip = full_label
                color = "black"
                if len(parts)  > 2:
                    if parts[2] == "inner":
                        display_label = parts[2:4]
                        tool_tip = parts[1] 
                        if len(parts) > 4:
                            tool_tip  = tool_tip + ":".join(parts[4:])
                            
                        pass
                    else:
                        display_label = parts[2]
                        tool_tip = parts[1]
                        if len(parts) > 3:
                            tool_tip  = tool_tip + ":".join(parts[3:])
                    color = color_map[parts[0]]
                print(f"{full_label} <==>  {display_label}<=> {tool_tip}")
                oval = canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="blue")
                btn = tk.Button(app, text='?', relief="flat", bg="lightblue", activebackground="lightblue")
                btn.place(x=x - 10, y=y - 10, width=15, height=15)  # Place the button on the canvas
                
                # Attach the tooltip
                Hovertip(btn, tool_tip)
                canvas.create_text(x-30, y, text=display_label, angle=90, font=("Arial", 10), fill="black")

            else:
                print("position not granted ", node)
                

    def draw_edges(self, canvas):
        for alink in self.links:
            # alink.id
            # alink.source
            # alink.target
            source_x = self.nodes[alink["source"]]['x']
            source_y = self.nodes[alink["source"]]['y']
            target_x = self.nodes[alink["target"]]['x']
            target_y = self.nodes[alink["target"]]['y']

            canvas.create_line(
                source_x, source_y,  # Center node coordinates
                target_x, target_y,  # Current node coordinates
                fill="black", width=1
            )     
                
                
                
        #     .append({
        #     "id": f"link-{self.link_id}",
        #     "source": self.node_map[source],
        #     "target": self.node_map[target],
        #     "label": f"{source} -> {target}"  # Label for the link
        # })
        #     canvas.create_line(
        #     1280, 720,  # Center node coordinates
        #     node["x"], node["y"],  # Current node coordinates
        #     fill="black", width=2
        # )

            
            
builder = task_graph_d3json()
root_task = "final"
import sys
if len(sys.argv) > 1: 
    builder.build_task_graph(root_task)

    builder.pickle_graph("task_dep.pickle")
else:
    
    builder.unpickle_graph("task_dep.pickle")

    builder.topological_sort()
    builder.postprocess()
    # # print(builder.level_map)
    builder.assign_position()



    # import tkinter as tk
    from idlelib.tooltip import Hovertip

    # Create the main application window
    app = tk.Tk()
    app.title("Circles with Tooltips")
    #Creates a turtle screen with a specified width (2560) and height (1440).

    app.geometry("2560x1440")  # Set the window size

    # Canvas for drawing circles
    canvas = tk.Canvas(app, width=2560, height=1440, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)


    # small canvas window
    # Function to create a smaller canvas in its own window
    # Conversion: 1 inch = 96 pixels (standard DPI)
    INCH_TO_PIXELS = 96
    legend_window_width = 2.37 * INCH_TO_PIXELS  # 5 inches wide
    legend_window_height = 4.5 * INCH_TO_PIXELS  # 5 inches high
    def create_movable_canvas():
        # Create a new Toplevel window
        small_window = tk.Toplevel(app)
        small_window.title("Small Canvas")
        small_window.geometry(f"legend_window_width * legend_window_height")  # 5 inches x 5 inches at 96 DPI
        small_window.configure(bg="lightgray")

        # Create a canvas in the new window
        small_canvas = tk.Canvas(small_window, width=legend_window_width, height=legend_window_height, bg="lightgray")
        small_canvas.pack(fill=tk.BOTH, expand=True)

        # Add elements to the smaller canvas
        small_canvas.create_rectangle(20, 20, 100, 100, fill="lightgreen", outline="green")
        small_canvas.create_text(60, 60, text="Small", font=("Arial", 12), fill="black")

        # Tooltip example
        btn = tk.Button(small_window, text="?", relief="flat", bg="lightgray", activebackground="lightgray")
        btn.place(x=20, y=150, width=20, height=20)
        Hovertip(btn, "This is a smaller canvas.")

    # Button to open the smaller canvas window
    #open_button = tk.Button(app, text="Open Small Canvas", command=create_movable_canvas)
    #open_button.place(x=50, y=50)

    builder.draw_edges(canvas)
    builder.draw_nodes(canvas)

    app.mainloop()
