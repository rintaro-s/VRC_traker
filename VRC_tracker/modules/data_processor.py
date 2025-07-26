import math
import mediapipe as mp
from config import ConfigManager
import time # timeモジュールをインポート

class DataProcessor:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager

        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh

        self.THUMB_TIP = self.mp_hands.HandLandmark.THUMB_TIP
        self.THUMB_MCP = self.mp_hands.HandLandmark.THUMB_MCP
        self.INDEX_FINGER_TIP = self.mp_hands.HandLandmark.INDEX_FINGER_TIP
        self.INDEX_FINGER_MCP = self.mp_hands.HandLandmark.INDEX_FINGER_MCP
        self.MIDDLE_FINGER_TIP = self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP
        self.MIDDLE_FINGER_MCP = self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP
        self.RING_FINGER_TIP = self.mp_hands.HandLandmark.RING_FINGER_TIP
        self.RING_FINGER_MCP = self.mp_hands.HandLandmark.RING_FINGER_MCP
        self.PINKY_TIP = self.mp_hands.HandLandmark.PINKY_TIP
        self.PINKY_MCP = self.mp_hands.HandLandmark.PINKY_MCP
        self.WRIST = self.mp_hands.HandLandmark.WRIST

        self.LEFT_EYE_UPPER = 159
        self.LEFT_EYE_LOWER = 145
        self.RIGHT_EYE_UPPER = 386
        self.RIGHT_EYE_LOWER = 374

        self.MOUTH_UPPER = 13
        self.MOUTH_LOWER = 14

        # Joy-Conの姿勢を保持するための変数 (簡易的な積分)
        self.joycon_orientation_l = [0.0, 0.0, 0.0] # Roll, Pitch, Yaw (ラジアン)
        self.joycon_orientation_r = [0.0, 0.0, 0.0]
        self.last_joycon_update_time = time.time()

    def _get_distance(self, p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def _calculate_finger_curl(self, landmarks, tip_idx, mcp_idx, finger_name):
        tip = landmarks.landmark[tip_idx]
        mcp = landmarks.landmark[mcp_idx]

        open_y_diff, closed_y_diff = self.config.get_hand_curl_thresholds(finger_name)

        current_y_diff = abs(tip.y - mcp.y)

        curl = 1.0 - ((current_y_diff - closed_y_diff) / (open_y_diff - closed_y_diff))
        curl = max(0.0, min(1.0, curl))

        return curl

    def process_hand_data(self, hand_results):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {} # Visualizerに送るデータ

        if not hand_results.multi_hand_landmarks:
            return osc_params, info_for_gui, visualizer_data

        visualizer_data["hand_landmarks"] = {}

        for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
            handedness = hand_results.multi_handedness[hand_idx].classification[0].label
            prefix = "Left" if handedness == "Left" else "Right"

            thumb_curl = self._calculate_finger_curl(hand_landmarks, self.THUMB_TIP, self.THUMB_MCP, "thumb")
            index_curl = self._calculate_finger_curl(hand_landmarks, self.INDEX_FINGER_TIP, self.INDEX_FINGER_MCP, "index")
            middle_curl = self._calculate_finger_curl(hand_landmarks, self.MIDDLE_FINGER_TIP, self.MIDDLE_FINGER_MCP, "middle")
            ring_curl = self._calculate_finger_curl(hand_landmarks, self.RING_FINGER_TIP, self.RING_FINGER_MCP, "ring")
            pinky_curl = self._calculate_finger_curl(hand_landmarks, self.PINKY_TIP, self.PINKY_MCP, "pinky")

            osc_params[f"/avatar/parameters/{prefix}HandThumbCurl"] = thumb_curl
            osc_params[f"/avatar/parameters/{prefix}HandIndexCurl"] = index_curl
            osc_params[f"/avatar/parameters/{prefix}HandMiddleCurl"] = middle_curl
            osc_params[f"/avatar/parameters/{prefix}HandRingCurl"] = ring_curl
            osc_params[f"/avatar/parameters/{prefix}HandPinkyCurl"] = pinky_curl

            info_for_gui[f"{prefix}HandThumbCurl"] = thumb_curl
            info_for_gui[f"{prefix}HandIndexCurl"] = index_curl
            info_for_gui[f"{prefix}HandMiddleCurl"] = middle_curl
            info_for_gui[f"{prefix}HandRingCurl"] = ring_curl
            info_for_gui[f"{prefix}HandPinkyCurl"] = pinky_curl

            fist_threshold, open_threshold = self.config.get_gesture_thresholds()
            avg_curl = (thumb_curl + index_curl + middle_curl + ring_curl + pinky_curl) / 5.0

            gesture_value = 2
            if avg_curl > fist_threshold:
                gesture_value = 1
            elif avg_curl < open_threshold:
                gesture_value = 0

            osc_params[f"/avatar/parameters/Gesture{prefix}"] = gesture_value
            info_for_gui[f"Gesture{prefix}"] = gesture_value

            # Visualizer用にランドマークを保存
            visualizer_data["hand_landmarks"][prefix] = hand_landmarks.landmark

        return osc_params, info_for_gui, visualizer_data

    def process_face_data(self, face_results):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {} # Visualizerに送るデータ (顔は今回は描画しないが、将来的な拡張のため)

        if not face_results.multi_face_landmarks:
            return osc_params, info_for_gui, visualizer_data

        for face_landmarks in face_results.multi_face_landmarks:
            left_eye_upper = face_landmarks.landmark[self.LEFT_EYE_UPPER]
            left_eye_lower = face_landmarks.landmark[self.LEFT_EYE_LOWER]
            right_eye_upper = face_landmarks.landmark[self.RIGHT_EYE_UPPER]
            right_eye_lower = face_landmarks.landmark[self.RIGHT_EYE_LOWER]

            left_eye_distance = self._get_distance(left_eye_upper, left_eye_lower)
            right_eye_distance = self._get_distance(right_eye_upper, right_eye_lower)

            eye_open_threshold, eye_closed_threshold = self.config.get_eye_thresholds()

            left_eye_openness = (left_eye_distance - eye_closed_threshold) / (eye_open_threshold - eye_closed_threshold)
            right_eye_openness = (right_eye_distance - eye_closed_threshold) / (eye_open_threshold - eye_closed_threshold)

            left_eye_openness = max(0.0, min(1.0, left_eye_openness))
            right_eye_openness = max(0.0, min(1.0, right_eye_openness))

            osc_params["/avatar/parameters/EyeLidL"] = left_eye_openness
            osc_params["/avatar/parameters/EyeLidR"] = right_eye_openness
            info_for_gui["EyeLidL"] = left_eye_openness
            info_for_gui["EyeLidR"] = right_eye_openness

            mouth_upper = face_landmarks.landmark[self.MOUTH_UPPER]
            mouth_lower = face_landmarks.landmark[self.MOUTH_LOWER]
            mouth_distance = self._get_distance(mouth_upper, mouth_lower)

            mouth_open_threshold, mouth_closed_threshold = self.config.get_mouth_thresholds()

            mouth_openness = (mouth_distance - mouth_closed_threshold) / (mouth_open_threshold - mouth_closed_threshold)
            mouth_openness = max(0.0, min(1.0, mouth_openness))

            osc_params["/avatar/parameters/MouthOpen"] = mouth_openness
            info_for_gui["MouthOpen"] = mouth_openness

        return osc_params, info_for_gui, visualizer_data

    def process_joycon_data(self, joycon_status):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {} # Visualizerに送るデータ
        visualizer_data["joycon_orientations"] = {}

        current_time = time.time()
        dt = current_time - self.last_joycon_update_time
        self.last_joycon_update_time = current_time

        gyro_sensitivity = self.config.get_gyro_sensitivity()

        if 'right' in joycon_status and joycon_status['right'] and 'gyro' in joycon_status['right']:
            gyro_r = joycon_status['right']['gyro']
            # ジャイロ値を積分して姿勢を更新 (簡易的な実装)
            # ジャイロ値はdeg/sなので、ラジアン/sに変換してdtを掛ける
            self.joycon_orientation_r[0] += math.radians(gyro_r[0]) * dt # Roll (X)
            self.joycon_orientation_r[1] += math.radians(gyro_r[1]) * dt # Pitch (Y)
            self.joycon_orientation_r[2] += math.radians(gyro_r[2]) * dt # Yaw (Z)

            osc_params["/avatar/parameters/RightHandYaw"] = self.joycon_orientation_r[2] * gyro_sensitivity
            osc_params["/avatar/parameters/RightHandPitch"] = self.joycon_orientation_r[1] * gyro_sensitivity
            osc_params["/avatar/parameters/RightHandRoll"] = self.joycon_orientation_r[0] * gyro_sensitivity
            info_for_gui["RightHandYaw"] = self.joycon_orientation_r[2] * gyro_sensitivity
            info_for_gui["RightHandPitch"] = self.joycon_orientation_r[1] * gyro_sensitivity
            info_for_gui["RightHandRoll"] = self.joycon_orientation_r[0] * gyro_sensitivity
            visualizer_data["joycon_orientations"]["Right"] = self.joycon_orientation_r

        if 'left' in joycon_status and joycon_status['left'] and 'gyro' in joycon_status['left']:
            gyro_l = joycon_status['left']['gyro']
            self.joycon_orientation_l[0] += math.radians(gyro_l[0]) * dt # Roll (X)
            self.joycon_orientation_l[1] += math.radians(gyro_l[1]) * dt # Pitch (Y)
            self.joycon_orientation_l[2] += math.radians(gyro_l[2]) * dt # Yaw (Z)

            osc_params["/avatar/parameters/LeftHandYaw"] = self.joycon_orientation_l[2] * gyro_sensitivity
            osc_params["/avatar/parameters/LeftHandPitch"] = self.joycon_orientation_l[1] * gyro_sensitivity
            osc_params["/avatar/parameters/LeftHandRoll"] = self.joycon_orientation_l[0] * gyro_sensitivity
            info_for_gui["LeftHandYaw"] = self.joycon_orientation_l[2] * gyro_sensitivity
            info_for_gui["LeftHandPitch"] = self.joycon_orientation_l[1] * gyro_sensitivity
            info_for_gui["LeftHandRoll"] = self.joycon_orientation_l[0] * gyro_sensitivity
            visualizer_data["joycon_orientations"]["Left"] = self.joycon_orientation_l

        if 'right' in joycon_status and joycon_status['right'] and 'stick' in joycon_status['right']:
            stick_r = joycon_status['right']['stick']
            osc_params["/avatar/parameters/RightStickX"] = stick_r[0]
            osc_params["/avatar/parameters/RightStickY"] = stick_r[1]
            info_for_gui["RightStickX"] = stick_r[0]
            info_for_gui["RightStickY"] = stick_r[1]
        
        if 'left' in joycon_status and joycon_status['left'] and 'stick' in joycon_status['left']:
            stick_l = joycon_status['left']['stick']
            osc_params["/avatar/parameters/LeftStickX"] = stick_l[0]
            osc_params["/avatar/parameters/LeftStickY"] = stick_l[1]
            info_for_gui["LeftStickX"] = stick_l[0]
            info_for_gui["LeftStickY"] = stick_l[1]

        if 'right' in joycon_status and joycon_status['right'] and 'buttons' in joycon_status['right']:
            buttons_r = joycon_status['right']['buttons']
            button_info = {}
            for button_name, is_pressed in buttons_r.items():
                osc_params[f"/avatar/parameters/RightJoyConButton{button_name}"] = is_pressed
                button_info[button_name] = is_pressed
            info_for_gui["RightJoyConButtons"] = button_info

        if 'left' in joycon_status and joycon_status['left'] and 'buttons' in joycon_status['left']:
            buttons_l = joycon_status['left']['buttons']
            button_info = {}
            for button_name, is_pressed in buttons_l.items():
                osc_params[f"/avatar/parameters/LeftJoyConButton{button_name}"] = is_pressed
                button_info[button_name] = is_pressed
            info_for_gui["LeftJoyConButtons"] = button_info

        return osc_params, info_for_gui, visualizer_data
