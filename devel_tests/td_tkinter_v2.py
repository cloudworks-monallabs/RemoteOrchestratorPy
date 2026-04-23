import tkinter as tk
from idlelib.tooltip import Hovertip

# Create the main application window
app = tk.Tk()
app.title("Circles with Tooltips")
#Creates a turtle screen with a specified width (2560) and height (1440).

app.geometry("2560x1440")  # Set the window size

# Canvas for drawing circles
canvas = tk.Canvas(app, width=2560, height=1440, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

# List of circles with positions, radius, and tooltip text
circles = [
    {"x": 200, "y": 150, "radius": 50, "tooltip": "This is Circle 1"},
    {"x": 400, "y": 300, "radius": 70, "tooltip": "This is Circle 2"},
    {"x": 600, "y": 450, "radius": 40, "tooltip": "This is Circle 3"},
]

# Draw circles and add tooltips
for circle in circles:
    # Draw a circle on the canvas
    x, y, r = circle["x"], circle["y"], circle["radius"]
    oval = canvas.create_oval(x - r, y - r, x + r, y + r, fill="lightblue", outline="blue")
    
    # Create a button in the center of the circle to hold the tooltip
    btn = tk.Button(app, text="?", relief="flat", bg="lightblue", activebackground="lightblue")
    btn.place(x=x - 10, y=y - 10, width=20, height=20)  # Place the button on the canvas
    
    # Attach the tooltip
    Hovertip(btn, circle["tooltip"])

# Run the application
app.mainloop()
