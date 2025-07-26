import configparser

class ConfigManager:
    def __init__(self, settings_path='settings.ini'):
        self.settings_path = settings_path
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        self.config.read(self.settings_path)

    def save_config(self):
        with open(self.settings_path, 'w') as configfile:
            self.config.write(configfile)

    def get_osc_host(self):
        return self.config.get('OSC', 'host', fallback='127.0.0.1')

    def set_osc_host(self, value):
        self.config.set('OSC', 'host', value)

    def get_osc_port(self):
        return self.config.getint('OSC', 'port', fallback=9000)

    def set_osc_port(self, value):
        self.config.set('OSC', 'port', str(value)) # configparser writes ints as strings

    def get_camera_device_id(self):
        return self.config.getint('Camera', 'device_id', fallback=0)

    def set_camera_device_id(self, value):
        self.config.set('Camera', 'device_id', str(value))

    # Hand Tracking Settings
    def get_hand_curl_thresholds(self, finger_name):
        open_key = f"{finger_name}_curl_open_y_diff"
        closed_key = f"{finger_name}_curl_closed_y_diff"
        return (
            self.config.getfloat('HandTracking', open_key, fallback=0.1),
            self.config.getfloat('HandTracking', closed_key, fallback=0.02)
        )

    def set_hand_curl_thresholds(self, finger_name, open_val, closed_val):
        self.config.set('HandTracking', f"{finger_name}_curl_open_y_diff", str(open_val))
        self.config.set('HandTracking', f"{finger_name}_curl_closed_y_diff", str(closed_val))

    def get_gesture_thresholds(self):
        return (
            self.config.getfloat('HandTracking', 'gesture_fist_threshold', fallback=0.8),
            self.config.getfloat('HandTracking', 'gesture_open_threshold', fallback=0.2)
        )

    def set_gesture_thresholds(self, fist_threshold, open_threshold):
        self.config.set('HandTracking', 'gesture_fist_threshold', str(fist_threshold))
        self.config.set('HandTracking', 'gesture_open_threshold', str(open_threshold))

    # Face Tracking Settings
    def get_eye_thresholds(self):
        return (
            self.config.getfloat('FaceTracking', 'eye_open_threshold', fallback=0.05),
            self.config.getfloat('FaceTracking', 'eye_closed_threshold', fallback=0.01)
        )

    def set_eye_thresholds(self, open_val, closed_val):
        self.config.set('FaceTracking', 'eye_open_threshold', str(open_val))
        self.config.set('FaceTracking', 'eye_closed_threshold', str(closed_val))

    def get_mouth_thresholds(self):
        return (
            self.config.getfloat('FaceTracking', 'mouth_open_threshold', fallback=0.04),
            self.config.getfloat('FaceTracking', 'mouth_closed_threshold', fallback=0.005)
        )

    def set_mouth_thresholds(self, open_val, closed_val):
        self.config.set('FaceTracking', 'mouth_open_threshold', str(open_val))
        self.config.set('FaceTracking', 'mouth_closed_threshold', str(closed_val))

    # Joy-Con Tracking Settings
    def get_gyro_sensitivity(self):
        return self.config.getfloat('JoyConTracking', 'gyro_sensitivity', fallback=0.01)

    def set_gyro_sensitivity(self, value):
        self.config.set('JoyConTracking', 'gyro_sensitivity', str(value))