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
    
dependecies = ["final"]
while True:
    dependecies = get_task_dependencies(dependecies[0])
    if len(dependecies)> 0:
        print(dependecies)
    else:
        break
