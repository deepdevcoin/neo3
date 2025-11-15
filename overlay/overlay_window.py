"""
Safe overlay window - doesn't steal focus
"""
from PyQt5 import QtWidgets, QtGui, QtCore
import mss


class OverlayWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # Get screen dimensions
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            self.screen_width = monitor["width"]
            self.screen_height = monitor["height"]
            self.screen_left = monitor["left"]
            self.screen_top = monitor["top"]
        
        # Get Qt screen info
        screen = QtWidgets.QApplication.primaryScreen()
        qt_geom = screen.geometry()
        qt_avail = screen.availableGeometry()
        
        # Calculate panel offset
        self.panel_offset_x = qt_avail.x() - qt_geom.x()
        self.panel_offset_y = qt_avail.y() - qt_geom.y()
        
        # Window flags - PASSIVE MODE (don't steal focus)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowDoesNotAcceptFocus  # Key: don't steal focus
        )
        
        # Transparency
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)  # Don't activate on show
        
        # Mouse passthrough
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        
        # No keyboard focus
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        
        # Shape storage
        self.shapes = []
        
        # Set geometry
        self.setGeometry(qt_geom)
        
        # Show WITHOUT activating
        self.show()
        
        print("✓ Overlay window (passive mode)")
    
    def add_circle(self, x: int, y: int):
        """Add circle (coordinates in screen space)"""
        adjusted_x = x - self.panel_offset_x
        adjusted_y = y - self.panel_offset_y
        
        self.shapes.append(("circle", (adjusted_x, adjusted_y)))
        self.update()
    
    def add_rect(self, x1: int, y1: int, x2: int, y2: int):
        """Add rectangle (coordinates in screen space)"""
        adjusted_x1 = x1 - self.panel_offset_x
        adjusted_y1 = y1 - self.panel_offset_y
        adjusted_x2 = x2 - self.panel_offset_x
        adjusted_y2 = y2 - self.panel_offset_y
        
        self.shapes.append(("rect", (adjusted_x1, adjusted_y1, adjusted_x2, adjusted_y2)))
        self.update()
    
    def clear_shapes(self):
        """Clear all shapes"""
        self.shapes = []
        self.update()
    
    def paintEvent(self, event):
        """Draw shapes"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Green pen for shapes
        pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 255), 4)
        painter.setPen(pen)
        
        for shape, data in self.shapes:
            if shape == "circle":
                x, y = data
                painter.drawEllipse(QtCore.QPoint(x, y), 20, 20)
                # Crosshair
                painter.drawLine(x-10, y, x+10, y)
                painter.drawLine(x, y-10, x, y+10)
            
            elif shape == "rect":
                x1, y1, x2, y2 = data
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        
        # Instructions (small, non-intrusive)
        if self.shapes:
            painter.setPen(QtGui.QColor(255, 255, 0, 200))
            painter.setFont(QtGui.QFont("Arial", 10))
            text = f"Overlay: {len(self.shapes)} shape(s)"
            painter.drawText(10, 20, text)