import json
import subprocess
import re

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
    print("Task dependencies:", dependencies)
    return dependencies[:-1]

def build_task_graph_with_labels_d3(root_task):
    """
    Build a task graph in D3.js format with labels for nodes and edges.

    Args:
        root_task (str): The root task label.
        get_task_dependencies (callable): A function that returns a list of dependencies for a given task label.

    Returns:
        str: JSON string for D3.js graph visualization.
    """
    nodes = []  # List of nodes
    links = []  # List of links
    node_map = {}  # Map to ensure unique nodes
    link_id = 1  # Unique ID for links

    def add_node(task_label):
        """Add a node to the graph if it doesn't already exist."""
        if task_label not in node_map:
            node_id = len(nodes) + 1
            node_map[task_label] = node_id
            nodes.append({"id": node_id, "name": task_label})

    def add_link(source, target):
        """Add a link between two nodes."""
        nonlocal link_id
        links.append({
            "id": f"link-{link_id}",
            "source": node_map[source],
            "target": node_map[target],
            "label": f"{source} -> {target}"  # Label for the link
        })
        link_id += 1

    # Start building the graph
    queue = [root_task]
    visited = set()

    while queue:
        current_task = queue.pop(0)
        if current_task in visited:
            continue
        visited.add(current_task)

        # Add the current task as a node
        add_node(current_task)

        # Get dependencies and add them to the graph
        dependencies = get_task_dependencies(current_task)
        for dep in dependencies:
            add_node(dep)
            add_link(current_task, dep)
            if dep not in visited:
                queue.append(dep)

    # Output the graph in D3.js format
    d3_graph = {
        "nodes": nodes,
        "links": links
    }
    return json.dumps(d3_graph, indent=2)

# Example usage


# Generate the graph
root_task = "final"
d3_graph_json = build_task_graph_with_labels_d3(root_task)

# Save to a file or print
with open("task_graph.json", "w") as f:
    f.write(d3_graph_json)

print("Generated D3.js graph JSON:")
print(d3_graph_json)
