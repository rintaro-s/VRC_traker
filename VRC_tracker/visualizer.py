import pyglet
import pyglet.gl as gl
import queue
import threading
import math
import mediapipe as mp # MediaPipeをインポート

class Visualizer(pyglet.window.Window):
    def __init__(self, data_queue):
        super().__init__(width=800, height=600, caption='VRC_traker 3D Visualizer', resizable=True)
        gl.glClearColor(0.2, 0.3, 0.4, 1.0)

        self.data_queue = data_queue
        self.tracking_data = {} # 最新のトラッキングデータを保持

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(60, self.width / self.height, 0.1, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (gl.GLfloat * 4)(0, 0, 1, 0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, (gl.GLfloat * 4)(0.5, 0.5, 0.5, 1))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, (gl.GLfloat * 4)(0.8, 0.8, 0.8, 1))

        gl.glEnable(gl.GL_DEPTH_TEST)

        pyglet.clock.schedule_interval(self.update, 1/60.0)

        # MediaPipe Poseの接続定義
        self.mp_pose = mp.solutions.pose

    def on_draw(self):
        self.clear()
        gl.glLoadIdentity()
        gl.gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

        self.draw_axes()

        if self.tracking_data:
            if "hand_landmarks" in self.tracking_data:
                self.draw_hands(self.tracking_data["hand_landmarks"])
            
            if "joycon_orientations" in self.tracking_data:
                self.draw_joycons(self.tracking_data["joycon_orientations"])

            if "pose_landmarks" in self.tracking_data:
                self.draw_pose(self.tracking_data["pose_landmarks"])

    def draw_axes(self):
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(1.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(1.0, 0.0, 0.0)
        gl.glColor3f(0.0, 1.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 1.0, 0.0)
        gl.glColor3f(0.0, 0.0, 1.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 1.0)
        gl.glEnd()

    def draw_hands(self, hand_landmarks_data):
        scale = 2.0

        for hand_type, landmarks in hand_landmarks_data.items():
            gl.glColor3f(1.0, 1.0, 0.0)
            gl.glPointSize(5.0)
            gl.glBegin(gl.GL_POINTS)
            for lm in landmarks:
                gl.glVertex3f(lm.x * scale - scale/2, lm.y * scale - scale/2, lm.z * scale - scale/2)
            gl.glEnd()

            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (9, 10), (10, 11), (11, 12),
                (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20)
            ]
            gl.glColor3f(0.0, 1.0, 1.0)
            gl.glLineWidth(2.0)
            gl.glBegin(gl.GL_LINES)
            for connection in connections:
                p1 = landmarks[connection[0]]
                p2 = landmarks[connection[1]]
                gl.glVertex3f(p1.x * scale - scale/2, p1.y * scale - scale/2, p1.z * scale - scale/2)
                gl.glVertex3f(p2.x * scale - scale/2, p2.y * scale - scale/2, p2.z * scale - scale/2)
            gl.glEnd()

    def draw_joycons(self, joycon_orientations):
        size = 0.2

        for jc_type, orientation in joycon_orientations.items():
            gl.glPushMatrix()
            
            if jc_type == "Left":
                gl.glTranslatef(-0.5, 0.0, 0.0)
                gl.glColor3f(0.0, 0.0, 1.0)
            else:
                gl.glTranslatef(0.5, 0.0, 0.0)
                gl.glColor3f(1.0, 0.0, 0.0)

            gl.glRotatef(math.degrees(orientation[0]), 1, 0, 0)
            gl.glRotatef(math.degrees(orientation[1]), 0, 1, 0)
            gl.glRotatef(math.degrees(orientation[2]), 0, 0, 1)

            vertices = [
                (-size, -size, -size), ( size, -size, -size), ( size,  size, -size), (-size,  size, -size),
                (-size, -size,  size), ( size, -size,  size), ( size,  size,  size), (-size,  size,  size)
            ]
            faces = [
                (0, 1, 2, 3), (4, 5, 6, 7),
                (0, 3, 7, 4), (1, 2, 6, 5),
                (0, 1, 5, 4), (3, 2, 6, 7)
            ]

            gl.glBegin(gl.GL_QUADS)
            for face in faces:
                for vertex_idx in face:
                    gl.glVertex3f(*vertices[vertex_idx])
            gl.glEnd()

            gl.glPopMatrix()

    def draw_pose(self, pose_landmarks):
        scale = 2.0 # スケールファクター

        gl.glColor3f(0.0, 1.0, 0.0) # 緑色でポーズを描画
        gl.glPointSize(5.0)
        gl.glBegin(gl.GL_POINTS)
        for lm in pose_landmarks:
            # 可視性スコアが低いランドマークは描画しない
            if lm.visibility > 0.5:
                gl.glVertex3f(lm.x * scale - scale/2, lm.y * scale - scale/2, lm.z * scale - scale/2)
        gl.glEnd()

        gl.glColor3f(0.0, 0.5, 1.0) # 水色でポーズの接続を描画
        gl.glLineWidth(2.0)
        gl.glBegin(gl.GL_LINES)
        for connection in self.mp_pose.POSE_CONNECTIONS:
            p1 = pose_landmarks[connection[0]]
            p2 = pose_landmarks[connection[1]]
            # 両方のランドマークの可視性スコアが高い場合のみ描画
            if p1.visibility > 0.5 and p2.visibility > 0.5:
                gl.glVertex3f(p1.x * scale - scale/2, p1.y * scale - scale/2, p1.z * scale - scale/2)
                gl.glVertex3f(p2.x * scale - scale/2, p2.y * scale - scale/2, p2.z * scale - scale/2)
        gl.glEnd()

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
