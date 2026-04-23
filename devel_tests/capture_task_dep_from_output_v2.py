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

def build_task_graph(root_task):
    # Initialize the graph structure
    graph = {
        "id": "root",
        "layoutOptions": {"algorithm": "layered"},
        "children": [],  # List of nodes
        "edges": []      # List of edges
    }

    # Set to track visited tasks
    encountered = set()
    # Function to add nodes and edges to the graph
    def add_to_graph(task, dependencies):
        if task not in visited:
            # Add the current task as a node
            graph["children"].append({"id": task, "width": 30, "height": 30})
            encountered.add(task)
        
        for dep in dependencies:
            if dep not in encountered:
                # Add the dependent task as a node
                graph["children"].append({"id": dep, "width": 30, "height": 30})
                encountered.add(dep)
            
            # Add an edge from the current task to the dependency
            edge_id = f"e_{task}_{dep}"
            graph["edges"].append({"id": edge_id, "sources": [task], "targets": [dep]})

    # BFS to traverse and build the graph
    queue = [root_task]
    explored = set()
    while queue:
        current_task = queue.pop(0)
        # Get dependencies for the current task
        dependencies = get_task_dependencies(current_task)
        explored.add(current_task)
        add_to_graph(current_task, dependencies)
        # Add dependencies to the queue for further exploration
        queue.extend(dep for dep in dependencies if dep not in explored)

    return graph

# Replace with your root task
root_task = "final"
graph = build_task_graph(root_task)

# Output the graph in JSON format
print(json.dumps(graph, indent=2))
