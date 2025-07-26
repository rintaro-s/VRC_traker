import time
import threading
import queue
import cv2

from config import ConfigManager
from modules.camera_tracker import CameraTracker
from modules.joycon_manager import JoyConManager
from modules.data_processor import DataProcessor
from modules.osc_sender import OSCSender
from gui import GUI
from visualizer import VisualizerThread # VisualizerThreadをインポート

class TrackingThread(threading.Thread):
    def __init__(self, config_manager, gui_data_queue, gui_command_queue, visualizer_data_queue):
        super().__init__()
        self.config = config_manager
        self.gui_data_queue = gui_data_queue
        self.gui_command_queue = gui_command_queue
        self.visualizer_data_queue = visualizer_data_queue # Visualizer用キュー
        self.running = True

        self.camera_tracker = None
        self.joycon_manager = None
        self.data_processor = None
        self.osc_sender = None
        self._initialize_modules()

    def _initialize_modules(self):
        if self.camera_tracker:
            self.camera_tracker.release()
        self.camera_tracker = CameraTracker(device_id=self.config.get_camera_device_id())

        if self.joycon_manager:
            self.joycon_manager.disconnect()
        self.joycon_manager = JoyConManager()

        self.data_processor = DataProcessor(self.config)
        
        if self.osc_sender:
            self.osc_sender.client.remote_address = (self.config.get_osc_host(), self.config.get_osc_port())
        else:
            self.osc_sender = OSCSender(self.config.get_osc_host(), self.config.get_osc_port())

    def run(self):
        print("Tracking thread started.")
        while self.running:
            try:
                try:
                    command = self.gui_command_queue.get_nowait()
                    if command["type"] == "APPLY_SETTINGS":
                        print("Applying settings from GUI...")
                        self.config.load_config()
                        self._initialize_modules()
                except queue.Empty:
                    pass

                hand_results, face_results, frame = self.camera_tracker.get_landmarks()
                joycon_status = self.joycon_manager.get_status()

                info_for_gui = {
                    "hands_detected": [],
                    "face_detected": False,
                    "joycon_connected": []
                }
                visualizer_data = {}

                # ハンドトラッキングデータの処理と送信
                if hand_results and hand_results.multi_hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                        handedness = hand_results.multi_handedness[hand_idx].classification[0].label
                        info_for_gui["hands_detected"].append(handedness)
                    
                    hand_osc_params, hand_info, hand_visualizer_data = self.data_processor.process_hand_data(hand_results)
                    for address, value in hand_osc_params.items():
                        self.osc_sender.send(address, value)
                    info_for_gui.update(hand_info)
                    visualizer_data.update(hand_visualizer_data)

                # フェイストラッキングデータの処理と送信
                if face_results and face_results.multi_face_landmarks:
                    info_for_gui["face_detected"] = True
                    face_osc_params, face_info, face_visualizer_data = self.data_processor.process_face_data(face_results)
                    for address, value in face_osc_params.items():
                        self.osc_sender.send(address, value)
                    info_for_gui.update(face_info)
                    visualizer_data.update(face_visualizer_data)

                # Joy-Conデータの処理と送信
                if joycon_status:
                    if 'left' in joycon_status:
                        info_for_gui["joycon_connected"].append("Left")
                    if 'right' in joycon_status:
                        info_for_gui["joycon_connected"].append("Right")

                    joycon_osc_params, joycon_info, joycon_visualizer_data = self.data_processor.process_joycon_data(joycon_status)
                    for address, value in joycon_osc_params.items():
                        self.osc_sender.send(address, value)
                    info_for_gui.update(joycon_info)
                    visualizer_data.update(joycon_visualizer_data)

                # カメラフレームをGUIに送信
                if frame is not None:
                    info_for_gui["frame"] = frame

                # GUIにデータを送信
                if not self.gui_data_queue.full():
                    self.gui_data_queue.put({"type": "TRACKING_DATA", "info": info_for_gui})

                # Visualizerにデータを送信
                if not self.visualizer_data_queue.full():
                    self.visualizer_data_queue.put({"type": "VISUALIZER_DATA", "data": visualizer_data})

                time.sleep(0.01)

            except Exception as e:
                print(f"Tracking thread error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        if self.camera_tracker:
            self.camera_tracker.release()
        if self.joycon_manager:
            self.joycon_manager.disconnect()
        print("Tracking thread stopped.")

class Application:
    def __init__(self):
        self.config = ConfigManager('VRC_tracker/settings.ini') # ここを変更
        self.gui_data_queue = queue.Queue(maxsize=1)
        self.gui_command_queue = queue.Queue(maxsize=1)
        self.visualizer_data_queue = queue.Queue(maxsize=1) # Visualizer用キュー

        self.tracking_thread = TrackingThread(self.config, self.gui_data_queue, self.gui_command_queue, self.visualizer_data_queue)
        self.gui = GUI(self.config, self.gui_data_queue, self.gui_command_queue)
        self.visualizer_thread = VisualizerThread(self.visualizer_data_queue) # Visualizerスレッド

    def run(self):
        self.tracking_thread.start()
        self.visualizer_thread.start() # Visualizerスレッドを開始
        self.gui.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gui.mainloop()

    def on_closing(self):
        print("Closing application...")
        self.tracking_thread.stop()
        self.tracking_thread.join()
        self.visualizer_thread.stop()
        self.visualizer_thread.join()
        self.gui.destroy()

if __name__ == "__main__":
    app = Application()
    app.run()
