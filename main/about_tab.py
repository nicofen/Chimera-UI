from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
import math
import random


def rotate_point_3d(x, y, z, rx, ry, rz):
    """Rotate a point in 3D space using Euler angles."""
    cosx, sinx = math.cos(rx), math.sin(rx)
    y2 = y * cosx - z * sinx
    z2 = y * sinx + z * cosx

    cosy, siny = math.cos(ry), math.sin(ry)
    x3 = x * cosy + z2 * siny
    z3 = -x * siny + z2 * cosy

    cosz, sinz = math.cos(rz), math.sin(rz)
    x4 = x3 * cosz - y2 * sinz
    y4 = x3 * sinz + y2 * cosz

    return x4, y4, z3


class AboutTab(QWidget):
    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

        self.num_points = 120
        self.points = []
        self.zoom = 2.0

        self.rx = 0
        self.ry = 0
        self.rz = 0

        self.vx = 0
        self.vy = 0
        self.vz = 0

        self.decay = 0.96

        self.generate_points()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

        self.dev_labels = [
            ("Sunset Excursions", "Owner / Lead Developer", "#d4af37"),
            ("Blobfishey", "Developer", "#00aaff"),
            ("Pineapple", "Developer", "#00aaff"),
            ("DiggingThrasher", "Developer", "#00aaff")
        ]

        self.last_mouse_pos = None

    def generate_points(self):
        """Generate random 3D points inside a sphere."""
        self.points = []
        for _ in range(self.num_points):
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = random.uniform(0.3, 1.0)

            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)

            self.points.append((x, y, z))

    def update_animation(self):
        """Apply inertia and update rotation."""
        self.rx += self.vx
        self.ry += self.vy
        self.rz += self.vz

        # Apply decay
        self.vx *= self.decay
        self.vy *= self.decay
        self.vz *= self.decay

        self.update()

    def mouseMoveEvent(self, event):
        """Mouse movement controls rotation velocity."""
        if self.last_mouse_pos is not None:
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()

            self.vy += dx * 0.0005   
            self.vx += dy * 0.0005   
            self.vz += dx * 0.0002

        self.last_mouse_pos = event.position()

    def draw_role_box(self, painter, x, y, width, height, name, role, color):
        painter.setBrush(QColor(10, 10, 20, 200))
        painter.setPen(QPen(QColor(color), 3))
        painter.drawRoundedRect(x, y, width, height, 14, 14)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(x, y + 10, width, height // 2, Qt.AlignCenter, name)

        painter.setPen(QColor(color))
        painter.setFont(QFont("Arial", 14))
        painter.drawText(x, y + height // 2, width, height // 2, Qt.AlignCenter, role)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        painter.fillRect(self.rect(), QColor(5, 5, 15))

        pen = QPen(QColor(0, 170, 255), 1)
        painter.setPen(pen)

        transformed = []
        for x, y, z in self.points:
            x2, y2, z2 = rotate_point_3d(x, y, z, self.rx, self.ry, self.rz)

            sx = cx + x2 * w * 0.4 * self.zoom
            sy = cy + y2 * h * 0.4 * self.zoom

            transformed.append((sx, sy, z2))

        for i in range(len(transformed)):
            for j in range(i + 1, len(transformed)):
                x1, y1, z1 = transformed[i]
                x2, y2, z2 = transformed[j]

                dist = math.hypot(x1 - x2, y1 - y2)
                if dist < w * 0.32:
                    alpha = max(20, 255 - int(dist * 0.7))
                    pen.setColor(QColor(0, 170, 255, alpha))
                    painter.setPen(pen)
                    painter.drawLine(x1, y1, x2, y2)

        spacing = h * 0.15
        start_y = h * 0.22
        box_w = int(w * 0.45)
        box_h = 80
        box_x = int((w - box_w) / 2)

        for i, (name, role, color) in enumerate(self.dev_labels):
            y = int(start_y + i * spacing)
            self.draw_role_box(painter, box_x, y, box_w, box_h, name, role, color)