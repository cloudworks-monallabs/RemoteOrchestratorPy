from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QToolTip
from PyQt5.QtCore import Qt
import sys

app = QApplication(sys.argv)

scene = QGraphicsScene()
view = QGraphicsView(scene)
view.setRenderHint(view.renderHints())

# Add a circle
circle = QGraphicsEllipseItem(50, 50, 100, 100)
circle.setToolTip("This is a circle")
scene.addItem(circle)

# Add a line
scene.addLine(0, 0, 200, 200)

view.show()
sys.exit(app.exec_())



