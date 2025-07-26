import pyglet
from pyglet.gl import * # ここを変更: すべてのOpenGL関数を直接インポート
import queue
import threading
import math

class Visualizer(pyglet.window.Window):
    def __init__(self, data_queue):
        super().__init__(width=800, height=600, caption='VRC_traker 3D Visualizer', resizable=True)
        glClearColor(0.2, 0.3, 0.4, 1.0) # gl. プレフィックスは不要

        self.data_queue = data_queue
        self.tracking_data = {} # 最新のトラッキングデータを保持

        glMatrixMode(GL_PROJECTION) # gl. プレフィックスは不要
        glLoadIdentity()
        gluPerspective(60, self.width / self.height, 0.1, 100.0) # glu. プレフィックスは不要
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(0, 0, 1, 0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (GLfloat * 4)(0.5, 0.5, 0.5, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(0.8, 0.8, 0.8, 1))

        glEnable(GL_DEPTH_TEST)

        pyglet.clock.schedule_interval(self.update, 1/60.0)

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

        self.draw_axes()

        if self.tracking_data:
            if "hand_landmarks" in self.tracking_data:
                self.draw_hands(self.tracking_data["hand_landmarks"])
            
            if "joycon_orientations" in self.tracking_data:
                self.draw_joycons(self.tracking_data["joycon_orientations"])

    def draw_axes(self):
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 1.0)
        glEnd()

    def draw_hands(self, hand_landmarks_data):
        scale = 2.0

        for hand_type, landmarks in hand_landmarks_data.items():
            glColor3f(1.0, 1.0, 0.0)
            glPointSize(5.0)
            glBegin(GL_POINTS)
            for lm in landmarks:
                glVertex3f(lm.x * scale - scale/2, lm.y * scale - scale/2, lm.z * scale - scale/2)
            glEnd()

            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (9, 10), (10, 11), (11, 12),
                (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20)
            ]
            glColor3f(0.0, 1.0, 1.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for connection in connections:
                p1 = landmarks[connection[0]]
                p2 = landmarks[connection[1]]
                glVertex3f(p1.x * scale - scale/2, p1.y * scale - scale/2, p1.z * scale - scale/2)
                glVertex3f(p2.x * scale - scale/2, p2.y * scale - scale/2, p2.z * scale - scale/2)
            glEnd()

    def draw_joycons(self, joycon_orientations):
        size = 0.2

        for jc_type, orientation in joycon_orientations.items():
            glPushMatrix()
            
            if jc_type == "Left":
                glTranslatef(-0.5, 0.0, 0.0)
                glColor3f(0.0, 0.0, 1.0)
            else:
                glTranslatef(0.5, 0.0, 0.0)
                glColor3f(1.0, 0.0, 0.0)

            glRotatef(math.degrees(orientation[0]), 1, 0, 0)
            glRotatef(math.degrees(orientation[1]), 0, 1, 0)
            glRotatef(math.degrees(orientation[2]), 0, 0, 1)

            vertices = [
                (-size, -size, -size), ( size, -size, -size), ( size,  size, -size), (-size,  size, -size),
                (-size, -size,  size), ( size, -size,  size), ( size,  size,  size), (-size,  size,  size)
            ]
            faces = [
                (0, 1, 2, 3), (4, 5, 6, 7),
                (0, 3, 7, 4), (1, 2, 6, 5),
                (0, 1, 5, 4), (3, 2, 6, 7)
            ]

            glBegin(GL_QUADS)
            for face in faces:
                for vertex_idx in face:
                    glVertex3f(*vertices[vertex_idx])
            glEnd()

            glPopMatrix()

    def update(self, dt):
        try:
            while True:
                data = self.data_queue.get_nowait()
                if data["type"] == "VISUALIZER_DATA":
                    self.tracking_data = data["data"]
        except queue.Empty:
            pass

    def run(self):
        pyglet.app.run()

    def close(self):
        pyglet.app.exit()
        super().close()

class VisualizerThread(threading.Thread):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.visualizer = None
        self.daemon = True

    def run(self):
        self.visualizer = Visualizer(self.data_queue)
        self.visualizer.run()

    def stop(self):
        if self.visualizer:
            self.visualizer.close()
