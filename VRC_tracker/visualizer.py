import pyglet
from pyglet.gl import (
    glClearColor, glMatrixMode, glLoadIdentity, gluPerspective, gluLookAt,
    glEnable, GL_LIGHTING, GL_LIGHT0, glLightfv, GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
    GL_DEPTH_TEST, glBegin, GL_LINES, glColor3f, glVertex3f, glEnd,
    glPointSize, GL_POINTS, glLineWidth, GL_QUADS, glPushMatrix, glPopMatrix,
    glTranslatef, glRotatef, GLfloat
)
import queue
import threading
import math

class Visualizer(pyglet.window.Window):
    def __init__(self, data_queue):
        super().__init__(width=800, height=600, caption='VRC_traker 3D Visualizer', resizable=True)
        glClearColor(0.2, 0.3, 0.4, 1.0) # 背景色

        self.data_queue = data_queue
        self.tracking_data = {} # 最新のトラッキングデータを保持

        # 視点設定
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, self.width / self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0) # カメラ位置 (x,y,z), ターゲット (x,y,z), アップベクトル (x,y,z)

        # 光源設定
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(0, 0, 1, 0)) # 平行光源
        glLightfv(GL_LIGHT0, GL_AMBIENT, (GLfloat * 4)(0.5, 0.5, 0.5, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(0.8, 0.8, 0.8, 1))

        glEnable(GL_DEPTH_TEST) # 深度テストを有効にする

        pyglet.clock.schedule_interval(self.update, 1/60.0) # 60FPSで更新

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0) # カメラ位置をリセット

        # 軸の描画
        self.draw_axes()

        # トラッキングデータの描画
        if self.tracking_data:
            # 手の描画
            if "hand_landmarks" in self.tracking_data:
                self.draw_hands(self.tracking_data["hand_landmarks"])
            
            # Joy-Conの描画
            if "joycon_orientations" in self.tracking_data:
                self.draw_joycons(self.tracking_data["joycon_orientations"])

    def draw_axes(self):
        glBegin(GL_LINES)
        # X軸 (赤)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        # Y軸 (緑)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        # Z軸 (青)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 1.0)
        glEnd()

    def draw_hands(self, hand_landmarks_data):
        # MediaPipeのランドマークは正規化されているため、適切なスケールに変換
        scale = 2.0 # 調整が必要なスケールファクター

        for hand_type, landmarks in hand_landmarks_data.items():
            glColor3f(1.0, 1.0, 0.0) # 黄色で手を描画
            glPointSize(5.0)
            glBegin(GL_POINTS)
            for lm in landmarks:
                glVertex3f(lm.x * scale - scale/2, lm.y * scale - scale/2, lm.z * scale - scale/2)
            glEnd()

            # 骨格の描画 (簡略版)
            # MediaPipeのHAND_CONNECTIONSを使って線を描画
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),  # 親指
                (0, 5), (5, 6), (6, 7), (7, 8),  # 人差し指
                (9, 10), (10, 11), (11, 12),     # 中指
                (13, 14), (14, 15), (15, 16),    # 薬指
                (0, 17), (17, 18), (18, 19), (19, 20) # 小指
            ]
            glColor3f(0.0, 1.0, 1.0) # シアンで骨格を描画
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for connection in connections:
                p1 = landmarks[connection[0]]
                p2 = landmarks[connection[1]]
                glVertex3f(p1.x * scale - scale/2, p1.y * scale - scale/2, p1.z * scale - scale/2)
                glVertex3f(p2.x * scale - scale/2, p2.y * scale - scale/2, p2.z * scale - scale/2)
            glEnd()

    def draw_joycons(self, joycon_orientations):
        # Joy-Conを簡易的な立方体で描画
        size = 0.2 # 立方体のサイズ

        for jc_type, orientation in joycon_orientations.items():
            glPushMatrix()
            
            # 位置 (仮: 左右に配置)
            if jc_type == "Left":
                glTranslatef(-0.5, 0.0, 0.0)
                glColor3f(0.0, 0.0, 1.0) # 左Joy-Conは青
            else: # Right
                glTranslatef(0.5, 0.0, 0.0)
                glColor3f(1.0, 0.0, 0.0) # 右Joy-Conは赤

            # 回転 (オイラー角から回転行列に変換して適用)
            # Pygletの回転は度数法
            glRotatef(math.degrees(orientation[0]), 1, 0, 0) # Roll (X軸)
            glRotatef(math.degrees(orientation[1]), 0, 1, 0) # Pitch (Y軸)
            glRotatef(math.degrees(orientation[2]), 0, 0, 1) # Yaw (Z軸)

            # 立方体の頂点
            vertices = [
                (-size, -size, -size), ( size, -size, -size), ( size,  size, -size), (-size,  size, -size),
                (-size, -size,  size), ( size, -size,  size), ( size,  size,  size), (-size,  size,  size)
            ]
            # 面のインデックス
            faces = [
                (0, 1, 2, 3), (4, 5, 6, 7), # 前後
                (0, 3, 7, 4), (1, 2, 6, 5), # 左右
                (0, 1, 5, 4), (3, 2, 6, 7)  # 上下
            ]

            glBegin(GL_QUADS)
            for face in faces:
                for vertex_idx in face:
                    glVertex3f(*vertices[vertex_idx])
            glEnd()

            glPopMatrix()

    def update(self, dt):
        # キューから最新のデータを取得
        try:
            while True: # キュー内のすべてのデータを消費
                data = self.data_queue.get_nowait()
                if data["type"] == "VISUALIZER_DATA":
                    self.tracking_data = data["data"]
        except queue.Empty:
            pass

    def run(self):
        pyglet.app.run()

    def close(self):
        # pyglet.app.exit() を呼び出してメインループを終了させる
        pyglet.app.exit()
        # ウィンドウ自体を閉じる
        super().close()

class VisualizerThread(threading.Thread):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.visualizer = None
        self.daemon = True # メインスレッド終了時に一緒に終了するように設定

    def run(self):
        self.visualizer = Visualizer(self.data_queue)
        self.visualizer.run()

    def stop(self):
        if self.visualizer:
            # pygletのメインループを終了させるために、メインスレッドから呼び出す必要がある
            # pyglet.clock.schedule_once(self.visualizer.close, 0) は別スレッドからだと問題を起こす可能性
            # 直接 close() を呼び出す
            self.visualizer.close()