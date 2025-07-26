from pyjoycon import JoyCon, get_L_id, get_R_id # ここを変更
import threading
import time

class JoyConManager:
    def __init__(self):
        self.joycon_l = None
        self.joycon_r = None
        self.status_l = {}
        self.status_r = {}
        self.lock_l = threading.Lock()
        self.lock_r = threading.Lock()

        try:
            l_id = get_L_id()
            if l_id:
                self.joycon_l = JoyCon(*l_id)
                print("Left Joy-Con connected.")
                threading.Thread(target=self._read_joycon_data, args=(self.joycon_l, self.status_l, self.lock_l), daemon=True).start()
            else:
                print("Left Joy-Con not found.")
        except (ValueError, TypeError, Exception) as e:
            print(f"Error connecting Left Joy-Con: {e}")

        try:
            r_id = get_R_id()
            if r_id:
                self.joycon_r = JoyCon(*r_id)
                print("Right Joy-Con connected.")
                threading.Thread(target=self._read_joycon_data, args=(self.joycon_r, self.status_r, self.lock_r), daemon=True).start()
            else:
                print("Right Joy-Con not found.")
        except (ValueError, TypeError, Exception) as e:
            print(f"Error connecting Right Joy-Con: {e}")

    def _read_joycon_data(self, joycon_instance, status_dict, lock):
        while True:
            try:
                current_status = joycon_instance.get_status()
                with lock:
                    status_dict.update(current_status)
            except Exception as e:
                print(f"Error reading Joy-Con data: {e}")
                break
            time.sleep(0.01)

    def get_status(self):
        combined_status = {}
        with self.lock_l:
            if self.status_l:
                combined_status['left'] = self.status_l.copy()
        with self.lock_r:
            if self.status_r:
                combined_status['right'] = self.status_r.copy()
        return combined_status

    def disconnect(self):
        if self.joycon_l:
            self.joycon_l.close()
            print("Left Joy-Con disconnected.")
        if self.joycon_r:
            self.joycon_r.close()
            print("Right Joy-Con disconnected.")