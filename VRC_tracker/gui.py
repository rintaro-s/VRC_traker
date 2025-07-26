import tkinter as tk
from tkinter import ttk, messagebox
import queue
import cv2
from PIL import Image, ImageTk

class GUI(tk.Tk):
    def __init__(self, config_manager, data_queue, command_queue):
        super().__init__()
        self.title("VRC_traker Settings")
        self.geometry("800x600")

        self.config_manager = config_manager
        self.data_queue = data_queue
        self.command_queue = command_queue

        self.create_widgets()
        self.load_settings_to_gui()
        self.after(100, self.update_gui_from_queue)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.create_settings_tab(self.settings_frame)

        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Real-time Info")
        self.create_info_tab(self.info_frame)

    def create_settings_tab(self, parent_frame):
        # OSC Settings
        osc_group = ttk.LabelFrame(parent_frame, text="OSC Settings")
        osc_group.pack(padx=10, pady=5, fill="x")
        tk.Label(osc_group, text="Host:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.osc_host_entry = tk.Entry(osc_group)
        self.osc_host_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(osc_group, text="Port:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.osc_port_entry = tk.Entry(osc_group)
        self.osc_port_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Camera Settings
        camera_group = ttk.LabelFrame(parent_frame, text="Camera Settings")
        camera_group.pack(padx=10, pady=5, fill="x")
        tk.Label(camera_group, text="Device ID:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.camera_id_entry = tk.Entry(camera_group)
        self.camera_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Hand Tracking Settings (簡易版)
        hand_group = ttk.LabelFrame(parent_frame, text="Hand Tracking Settings")
        hand_group.pack(padx=10, pady=5, fill="x")
        tk.Label(hand_group, text="Gesture Fist Threshold:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.hand_fist_threshold_entry = tk.Entry(hand_group)
        self.hand_fist_threshold_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(hand_group, text="Gesture Open Threshold:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.hand_open_threshold_entry = tk.Entry(hand_group)
        self.hand_open_threshold_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Face Tracking Settings (簡易版)
        face_group = ttk.LabelFrame(parent_frame, text="Face Tracking Settings")
        face_group.pack(padx=10, pady=5, fill="x")
        tk.Label(face_group, text="Eye Open Threshold:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.eye_open_threshold_entry = tk.Entry(face_group)
        self.eye_open_threshold_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(face_group, text="Eye Closed Threshold:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.eye_closed_threshold_entry = tk.Entry(face_group)
        self.eye_closed_threshold_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Joy-Con Tracking Settings
        joycon_group = ttk.LabelFrame(parent_frame, text="Joy-Con Tracking Settings")
        joycon_group.pack(padx=10, pady=5, fill="x")
        tk.Label(joycon_group, text="Gyro Sensitivity:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.gyro_sensitivity_entry = tk.Entry(joycon_group)
        self.gyro_sensitivity_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Pose Tracking Settings
        pose_group = ttk.LabelFrame(parent_frame, text="Pose Tracking Settings")
        pose_group.pack(padx=10, pady=5, fill="x")
        tk.Label(pose_group, text="Min Detection Confidence:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.pose_min_detection_confidence_entry = tk.Entry(pose_group)
        self.pose_min_detection_confidence_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(pose_group, text="Min Tracking Confidence:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.pose_min_tracking_confidence_entry = tk.Entry(pose_group)
        self.pose_min_tracking_confidence_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Arm OSC Parameters (表示のみ、変更はsettings.iniで)
        arm_osc_group = ttk.LabelFrame(parent_frame, text="Arm OSC Parameters (Read-only)")
        arm_osc_group.pack(padx=10, pady=5, fill="x")
        
        params = [
            "left_shoulder_x_param", "left_shoulder_y_param", "left_shoulder_z_param",
            "right_shoulder_x_param", "right_shoulder_y_param", "right_shoulder_z_param",
            "left_elbow_bend_param", "right_elbow_bend_param"
        ]
        for i, param_name in enumerate(params):
            tk.Label(arm_osc_group, text=f"{param_name}:").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            param_value = self.config_manager.get_arm_osc_parameter(param_name)
            tk.Label(arm_osc_group, text=param_value).grid(row=i, column=1, padx=5, pady=2, sticky="w")


        # Apply and Save Buttons
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Apply Settings", command=self.apply_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side="left", padx=5)

    def create_info_tab(self, parent_frame):
        # カメラプレビュー
        self.camera_canvas = tk.Canvas(parent_frame, bg="black", width=640, height=480)
        self.camera_canvas.pack(pady=10)

        # Joy-Con接続状態表示
        joycon_status_frame = ttk.LabelFrame(parent_frame, text="Joy-Con Connection Status")
        joycon_status_frame.pack(padx=10, pady=5, fill="x")
        self.left_joycon_status_label = tk.Label(joycon_status_frame, text="Left Joy-Con: Disconnected", fg="red")
        self.left_joycon_status_label.pack(anchor="w")
        self.right_joycon_status_label = tk.Label(joycon_status_frame, text="Right Joy-Con: Disconnected", fg="red")
        self.right_joycon_status_label.pack(anchor="w")

        # トラッキング情報表示エリア
        info_group = ttk.LabelFrame(parent_frame, text="Tracking Information")
        info_group.pack(padx=10, pady=5, fill="both", expand=True)

        self.info_text = tk.Text(info_group, wrap="word", height=10, state="disabled")
        self.info_text.pack(fill="both", expand=True)

    def load_settings_to_gui(self):
        # OSC
        self.osc_host_entry.delete(0, tk.END)
        self.osc_host_entry.insert(0, self.config_manager.get_osc_host())
        self.osc_port_entry.delete(0, tk.END)
        self.osc_port_entry.insert(0, self.config_manager.get_osc_port())

        # Camera
        self.camera_id_entry.delete(0, tk.END)
        self.camera_id_entry.insert(0, self.config_manager.get_camera_device_id())

        # Hand Tracking
        fist_thresh, open_thresh = self.config_manager.get_gesture_thresholds()
        self.hand_fist_threshold_entry.delete(0, tk.END)
        self.hand_fist_threshold_entry.insert(0, fist_thresh)
        self.hand_open_threshold_entry.delete(0, tk.END)
        self.hand_open_threshold_entry.insert(0, open_thresh)

        # Face Tracking
        eye_open, eye_closed = self.config_manager.get_eye_thresholds()
        self.eye_open_threshold_entry.delete(0, tk.END)
        self.eye_open_threshold_entry.insert(0, eye_open)
        self.eye_closed_threshold_entry.delete(0, tk.END)
        self.eye_closed_threshold_entry.insert(0, eye_closed)

        # Joy-Con Tracking
        self.gyro_sensitivity_entry.delete(0, tk.END)
        self.gyro_sensitivity_entry.insert(0, self.config_manager.get_gyro_sensitivity())

        # Pose Tracking
        self.pose_min_detection_confidence_entry.delete(0, tk.END)
        self.pose_min_detection_confidence_entry.insert(0, self.config_manager.get_pose_min_detection_confidence())
        self.pose_min_tracking_confidence_entry.delete(0, tk.END)
        self.pose_min_tracking_confidence_entry.insert(0, self.config_manager.get_pose_min_tracking_confidence())

    def apply_settings(self):
        try:
            # OSC
            self.config_manager.set_osc_host(self.osc_host_entry.get())
            self.config_manager.set_osc_port(int(self.osc_port_entry.get()))

            # Camera
            self.config_manager.set_camera_device_id(int(self.camera_id_entry.get()))

            # Hand Tracking
            self.config_manager.set_gesture_thresholds(
                float(self.hand_fist_threshold_entry.get()),
                float(self.hand_open_threshold_entry.get())
            )

            # Face Tracking
            self.config_manager.set_eye_thresholds(
                float(self.eye_open_threshold_entry.get()),
                float(self.eye_closed_threshold_entry.get())
            )
            self.config_manager.set_mouth_thresholds(
                self.config_manager.get_mouth_thresholds()[0],
                self.config_manager.get_mouth_thresholds()[1]
            )

            # Joy-Con Tracking
            self.config_manager.set_gyro_sensitivity(float(self.gyro_sensitivity_entry.get()))

            # Pose Tracking
            self.config_manager.set_pose_min_detection_confidence(float(self.pose_min_detection_confidence_entry.get()))
            self.config_manager.set_pose_min_tracking_confidence(float(self.pose_min_tracking_confidence_entry.get()))

            self.command_queue.put({"type": "APPLY_SETTINGS"})
            messagebox.showinfo("Settings", "Settings applied successfully! (Not yet saved to file)")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def save_settings(self):
        self.apply_settings()
        self.config_manager.save_config()
        messagebox.showinfo("Settings", "Settings saved to file!")

    def update_gui_from_queue(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                if data["type"] == "TRACKING_DATA":
                    self.update_info_display(data["info"])
                    if "frame" in data:
                        self.update_camera_preview(data["frame"])
                    self.update_joycon_status_display(data["info"].get("joycon_connected", []))
                elif data["type"] == "OSC_SENT":
                    pass
        except queue.Empty:
            pass
        finally:
            self.after(100, self.update_gui_from_queue)

    def update_camera_preview(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = image.resize((640, 480), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(image=image)
        self.camera_canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

    def update_info_display(self, info):
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        
        display_str = "--- Tracking Information ---\n"
        if info.get("hands_detected"):
            display_str += f"Hands Detected: {', '.join(info['hands_detected'])}\n"
            for hand_type in ["Left", "Right"]:
                if f"{hand_type}HandThumbCurl" in info:
                    display_str += f"  {hand_type} Hand:\n"
                    display_str += f"    Thumb Curl: {info.get(f'{hand_type}HandThumbCurl'):.2f}\n"
                    display_str += f"    Index Curl: {info.get(f'{hand_type}HandIndexCurl'):.2f}\n"
                    display_str += f"    Middle Curl: {info.get(f'{hand_type}HandMiddleCurl'):.2f}\n"
                    display_str += f"    Ring Curl: {info.get(f'{hand_type}HandRingCurl'):.2f}\n"
                    display_str += f"    Pinky Curl: {info.get(f'{hand_type}HandPinkyCurl'):.2f}\n"
                    display_str += f"    Gesture: {info.get(f'Gesture{hand_type}')}\n"
        else:
            display_str += "Hands: Not detected\n"

        if info.get("face_detected"):
            display_str += "Face Detected: Yes\n"
            display_str += f"  EyeLidL: {info.get('EyeLidL'):.2f}\n"
            display_str += f"  EyeLidR: {info.get('EyeLidR'):.2f}\n"
            display_str += f"  MouthOpen: {info.get('MouthOpen'):.2f}\n"
        else:
            display_str += "Face: Not detected\n"

        if info.get("pose_detected"):
            display_str += "Pose Detected: Yes\n"
            display_str += f"  Left Shoulder X: {info.get('LeftShoulderX'):.2f}\n"
            display_str += f"  Left Shoulder Y: {info.get('LeftShoulderY'):.2f}\n"
            display_str += f"  Left Shoulder Z: {info.get('LeftShoulderZ'):.2f}\n"
            display_str += f"  Right Shoulder X: {info.get('RightShoulderX'):.2f}\n"
            display_str += f"  Right Shoulder Y: {info.get('RightShoulderY'):.2f}\n"
            display_str += f"  Right Shoulder Z: {info.get('RightShoulderZ'):.2f}\n"
            display_str += f"  Left Elbow Bend: {info.get('LeftElbowBend'):.2f}\n"
            display_str += f"  Right Elbow Bend: {info.get('RightElbowBend'):.2f}\n"
        else:
            display_str += "Pose: Not detected\n"

        self.info_text.insert(tk.END, display_str)
        self.info_text.config(state="disabled")

    def update_joycon_status_display(self, connected_joycons):
        if "Left" in connected_joycons:
            self.left_joycon_status_label.config(text="Left Joy-Con: Connected", fg="green")
        else:
            self.left_joycon_status_label.config(text="Left Joy-Con: Disconnected", fg="red")
        
        if "Right" in connected_joycons:
            self.right_joycon_status_label.config(text="Right Joy-Con: Connected", fg="green")
        else:
            self.right_joycon_status_label.config(text="Right Joy-Con: Disconnected", fg="red")