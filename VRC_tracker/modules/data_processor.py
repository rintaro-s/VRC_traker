import math
import mediapipe as mp
from config import ConfigManager
import time

class DataProcessor:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager

        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose # MediaPipe Poseを初期化

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

        self.joycon_orientation_l = [0.0, 0.0, 0.0]
        self.joycon_orientation_r = [0.0, 0.0, 0.0]
        self.last_joycon_update_time = time.time()

    def _get_distance(self, p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def _calculate_angle(self, p1, p2, p3):
        """3点から角度を計算 (p2が頂点)"""
        # ベクトルを計算
        vec1 = [p1.x - p2.x, p1.y - p2.y, p1.z - p2.z]
        vec2 = [p3.x - p2.x, p3.y - p2.y, p3.z - p2.z]

        # ドット積とベクトルの大きさ
        dot_product = vec1[0]*vec2[0] + vec1[1]*vec2[1] + vec1[2]*vec2[2]
        magnitude1 = math.sqrt(vec1[0]**2 + vec1[1]**2 + vec1[2]**2)
        magnitude2 = math.sqrt(vec2[0]**2 + vec2[1]**2 + vec2[2]**2)

        # コサインを計算し、アークコサインで角度を求める
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0 # ゼロ除算を避ける
        
        cosine_angle = dot_product / (magnitude1 * magnitude2)
        # 浮動小数点誤差で範囲外になる可能性があるのでクランプ
        cosine_angle = max(-1.0, min(1.0, cosine_angle))
        angle_radians = math.acos(cosine_angle)
        return math.degrees(angle_radians) # 度数で返す

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
        visualizer_data = {}

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

            visualizer_data["hand_landmarks"][prefix] = hand_landmarks.landmark

        return osc_params, info_for_gui, visualizer_data

    def process_face_data(self, face_results):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {}

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

    def process_pose_data(self, pose_results):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {}
        
        if not pose_results.pose_landmarks:
            return osc_params, info_for_gui, visualizer_data

        landmarks = pose_results.pose_landmarks.landmark
        visualizer_data["pose_landmarks"] = landmarks

        # 肩の回転 (簡易的な例: 左右の肩のY座標の差をX軸回転にマッピング)
        # VRChatのアバターに合わせて調整が必要
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        
        # 左肩の回転 (例: 肩と肘の相対位置から計算)
        # X軸回転 (腕を前後に振る)
        # Y軸回転 (腕を左右に開く)
        # Z軸回転 (腕をひねる)
        # ここでは簡易的に、肩と肘のY座標の差をX軸回転にマッピング
        # 実際のVRChatアバターのボーン構造に合わせて、より複雑な計算が必要
        
        # 左肩のX軸回転 (腕を前後に振る)
        # 肘が肩より前にあるか後ろにあるかで判断
        left_shoulder_x_angle = (left_elbow.z - left_shoulder.z) * 100 # 適当なスケール
        osc_params[self.config.get_arm_osc_parameter("left_shoulder_x_param")] = left_shoulder_x_angle
        info_for_gui["LeftShoulderX"] = left_shoulder_x_angle

        # 左肩のY軸回転 (腕を左右に開く)
        # 肘が肩より外側にあるか内側にあるかで判断
        left_shoulder_y_angle = (left_elbow.x - left_shoulder.x) * 100
        osc_params[self.config.get_arm_osc_parameter("left_shoulder_y_param")] = left_shoulder_y_angle
        info_for_gui["LeftShoulderY"] = left_shoulder_y_angle

        # 左肩のZ軸回転 (腕をひねる) - 簡易版
        # 手首と肘のY座標の差をZ軸回転にマッピング
        left_shoulder_z_angle = (left_wrist.y - left_elbow.y) * 100
        osc_params[self.config.get_arm_osc_parameter("left_shoulder_z_param")] = left_shoulder_z_angle
        info_for_gui["LeftShoulderZ"] = left_shoulder_z_angle

        # 右肩も同様
        right_shoulder_x_angle = (right_elbow.z - right_shoulder.z) * 100
        osc_params[self.config.get_arm_osc_parameter("right_shoulder_x_param")] = right_shoulder_x_angle
        info_for_gui["RightShoulderX"] = right_shoulder_x_angle

        right_shoulder_y_angle = (right_elbow.x - right_shoulder.x) * 100
        osc_params[self.config.get_arm_osc_parameter("right_shoulder_y_param")] = right_shoulder_y_angle
        info_for_gui["RightShoulderY"] = right_shoulder_y_angle

        right_shoulder_z_angle = (right_wrist.y - right_elbow.y) * 100
        osc_params[self.config.get_arm_osc_parameter("right_shoulder_z_param")] = right_shoulder_z_angle
        info_for_gui["RightShoulderZ"] = right_shoulder_z_angle

        # 肘の曲がり具合 (角度を計算)
        # 左肘: 肩-肘-手首の角度
        left_elbow_angle = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
        # 角度を0-1の範囲に正規化 (例: 180度(伸びている) -> 0, 0度(完全に曲がっている) -> 1)
        # 実際のVRChatアバターのブレンドシェイプやボーンの回転に合わせて調整
        normalized_left_elbow_bend = (180 - left_elbow_angle) / 180.0
        osc_params[self.config.get_arm_osc_parameter("left_elbow_bend_param")] = normalized_left_elbow_bend
        info_for_gui["LeftElbowBend"] = normalized_left_elbow_bend

        # 右肘も同様
        right_elbow_angle = self._calculate_angle(right_shoulder, right_elbow, right_wrist)
        normalized_right_elbow_bend = (180 - right_elbow_angle) / 180.0
        osc_params[self.config.get_arm_osc_parameter("right_elbow_bend_param")] = normalized_right_elbow_bend
        info_for_gui["RightElbowBend"] = normalized_right_elbow_bend

        return osc_params, info_for_gui, visualizer_data

    def process_joycon_data(self, joycon_status):
        osc_params = {}
        info_for_gui = {}
        visualizer_data = {}
        visualizer_data["joycon_orientations"] = {}

        current_time = time.time()
        dt = current_time - self.last_joycon_update_time
        self.last_joycon_update_time = current_time

        gyro_sensitivity = self.config.get_gyro_sensitivity()

        if 'right' in joycon_status and joycon_status['right'] and 'gyro' in joycon_status['right']:
            gyro_r = joycon_status['right']['gyro']
            self.joycon_orientation_r[0] += math.radians(gyro_r[0]) * dt
            self.joycon_orientation_r[1] += math.radians(gyro_r[1]) * dt
            self.joycon_orientation_r[2] += math.radians(gyro_r[2]) * dt

            osc_params["/avatar/parameters/RightHandYaw"] = self.joycon_orientation_r[2] * gyro_sensitivity
            osc_params["/avatar/parameters/RightHandPitch"] = self.joycon_orientation_r[1] * gyro_sensitivity
            osc_params["/avatar/parameters/RightHandRoll"] = self.joycon_orientation_r[0] * gyro_sensitivity
            info_for_gui["RightHandYaw"] = self.joycon_orientation_r[2] * gyro_sensitivity
            info_for_gui["RightHandPitch"] = self.joycon_orientation_r[1] * gyro_sensitivity
            info_for_gui["RightHandRoll"] = self.joycon_orientation_r[0] * gyro_sensitivity
            visualizer_data["joycon_orientations"]["Right"] = self.joycon_orientation_r

        if 'left' in joycon_status and joycon_status['left'] and 'gyro' in joycon_status['left']:
            gyro_l = joycon_status['left']['gyro']
            self.joycon_orientation_l[0] += math.radians(gyro_l[0]) * dt
            self.joycon_orientation_l[1] += math.radians(gyro_l[1]) * dt
            self.joycon_orientation_l[2] += math.radians(gyro_l[2]) * dt

            osc_params["/avatar/parameters/LeftHandYaw"] = self.joycon_orientation_l[2] * gyro_sensitivity
            osc_params["/avatar/parameters/LeftHandPitch"] = self.joycon_orientation_l[1] * gyro_sensitivity
            osc_params["/avatar/parameters/LeftHandRoll"] = self.joycon_orientation_l[0] * gyro_sensitivity
            info_for_gui["LeftHandYaw"] = self.joycon_orientation_l[2] * gyro_sensitivity
            info_for_gui["LeftHandPitch"] = self.joycon_orientation_l[1] * gyro_sensitivity
            info_for_gui["LeftHandRoll"] = self.joycon_orientation_l[0] * gyro_sensitivity
            visualizer_data["joycon_orientations"]["Left"] = self.joycon_orientation_l

        if 'right' in joycon_status and joycon_status['right'] and 'stick' in joycon_status['right'] and joycon_status['right']['stick'] is not None:
            stick_r = joycon_status['right']['stick']
            osc_params["/avatar/parameters/RightStickX"] = stick_r[0]
            osc_params["/avatar/parameters/RightStickY"] = stick_r[1]
            info_for_gui["RightStickX"] = stick_r[0]
            info_for_gui["RightStickY"] = stick_r[1]
        
        if 'left' in joycon_status and joycon_status['left'] and 'stick' in joycon_status['left'] and joycon_status['left']['stick'] is not None:
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