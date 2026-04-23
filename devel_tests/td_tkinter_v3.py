import tkinter as tk
from idlelib.tooltip import Hovertip

# Create the main application window
app = tk.Tk()
app.title("Nodes with Tooltips")
app.geometry("2560x1440")  # Set the window size

# Create the canvas for drawing
canvas = tk.Canvas(app, width=2560, height=1440, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

# Circle radius
r = 20

# List of nodes with positions, IDs, and names
nodes = [
    {"id": "C", "name": "Center Node", "x": 1280, "y": 720},  # Center
    {"id": "TL", "name": "Top Left Node", "x": 100, "y": 100},  # Top Left
    {"id": "TR", "name": "Top Right Node", "x": 2460, "y": 100},  # Top Right
    {"id": "BL", "name": "Bottom Left Node", "x": 100, "y": 1340},  # Bottom Left
    {"id": "BR", "name": "Bottom Right Node", "x": 2460, "y": 1340},  # Bottom Right
]

# Add nodes to the canvas
for node in nodes:
    x, y = node["x"], node["y"]

    # Draw a circle for the node
    canvas.create_oval(x - r, y - r, x + r, y + r, fill="lightblue", outline="blue")

    # Create a button in the center of the circle for the tooltip
    btn = tk.Button(app, text=node["id"], relief="flat", bg="lightblue", activebackground="lightblue")
    btn.place(x=x - 10, y=y - 10, width=20, height=20)  # Adjust the button size and position

    # Attach the tooltip to the button
    Hovertip(btn, node["name"])

# Run the application
app.mainloop()

# for node in nodes:
#     if node["id"] != "C":  # Skip the center node for itself
#         # Draw a line from the center node to the current node
#         canvas.create_line(
#             1280, 720,  # Center node coordinates
#             node["x"], node["y"],  # Current node coordinates
#             fill="black", width=2
#         )






