import cv2
import mediapipe as mp

class CameraTracker:
    def __init__(self, device_id=0, pose_min_detection_confidence=0.5, pose_min_tracking_confidence=0.5):
        self.cap = None
        self.pose_min_detection_confidence = pose_min_detection_confidence
        self.pose_min_tracking_confidence = pose_min_tracking_confidence

        self.cap = cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            print(f"Warning: Could not open video device {device_id}. Attempting auto-detection...")
            found_camera = False
            for i in range(5): # ID 0から4までを試す (必要に応じて範囲を広げてください)
                print(f"Attempting to open camera with ID: {i}")
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    print(f"Successfully opened video device {i}.")
                    found_camera = True
                    break
                else:
                    self.cap.release() # 開けなかった場合は解放
            if not found_camera:
                print("Error: No working camera found. Please check camera connections.")
                self.cap = None # カメラが見つからなかった場合はNoneを設定
                return
        else:
            print(f"Successfully opened video device {device_id}.")

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        # MediaPipe Poseの初期化
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=self.pose_min_detection_confidence,
            min_tracking_confidence=self.pose_min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def get_landmarks(self):
        if self.cap is None:
            return None, None, None, None # hand_results, face_results, pose_results, frame

        success, frame = self.cap.read()
        if not success:
            print("Warning: Failed to read frame from camera.")
            return None, None, None, None

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        hand_results = self.hands.process(image_rgb)
        face_results = self.face_mesh.process(image_rgb)
        pose_results = self.pose.process(image_rgb) # ポーズの検出

        # 検出結果をフレームに描画 (GUIプレビュー用)
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1)
                )
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2)
                )
        # ポーズのランドマークを描画
        if pose_results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        return hand_results, face_results, pose_results, frame

    def release(self):
        if self.cap:
            self.cap.release()
            print("Camera released.")