import time, cv2, win32api, win32con, win32gui, tkinter as tk
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

print("Initializing R.I.O AI Virtual Mouse Engine (Fixed Variables)...")

base_options = python.BaseOptions(model_asset_path="C:/Users/izuishaalayshazaibu/Desktop/izan-VScode/Mouse1/hand_landmarker.task")
options = vision.HandLandmarkerOptions(
    base_options=base_options, 
    running_mode=vision.RunningMode.VIDEO, 
    num_hands=1, 
    min_hand_detection_confidence=0.4, 
    min_hand_presence_confidence=0.4
)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

root = tk.Tk()
screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
root.destroy()

# FULL CANVAS ENVELOPE
box_h = 0.85
box_w = 0.95
min_x, max_x = (1.0 - box_w)/2, (1.0 - box_w)/2 + box_w
min_y, max_y = (1.0 - box_h)/2, (1.0 - box_h)/2 + box_h

prev_x, prev_y = None, None
left_cnt, right_cnt = 0, 0
last_click_time = 0
swipe_x_hist = []

SCROLL_SPEED_MULTIPLIER = 35 
BOX_CENTER_Y = (min_y + max_y) / 2

win_name = "R.I.O AI"
cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)

with vision.HandLandmarker.create_from_options(options) as landmarker:
    window_reconfigured = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        fh, fw, _ = frame.shape
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))
        
        cv2.rectangle(frame, (int(min_x*fw), int(min_y*fh)), (int(max_x*fw), int(max_y*fh)), (255, 255, 255), 1, cv2.LINE_AA)
        
        if result.hand_landmarks:
            for hl in result.hand_landmarks:
                get_p = lambda idx: (int(hl[idx].x * fw), int(hl[idx].y * fh))
                
                for i in range(21):
                    cv2.circle(frame, get_p(i), 4, (255, 255, 255), -1, cv2.LINE_AA)
                
                connections = [
                    (0,1), (1,2), (2,3), (3,4), (0,5), (5,6), (6,7), (7,8),
                    (5,9), (9,10), (10,11), (11,12), (9,13), (13,14), (14,15), (15,16),
                    (13,17), (17,18), (18,19), (19,20), (0,17)
                ]
                for start, end in connections:
                    cv2.line(frame, get_p(start), get_p(end), (255, 255, 255), 2, cv2.LINE_AA)
                
                # Unpack landmarks
                t_tip_x, t_tip_y = hl[4].x, hl[4].y
                i_tip_x, i_tip_y = hl[8].x, hl[8].y
                i_mcp_x, i_mcp_y = hl[5].x, hl[5].y
                i_pip_x, i_pip_y = hl[6].x, hl[6].y
                m_tip_y = hl[12].y
                m_pip_y = hl[10].y
                r_tip_y = hl[16].y
                r_pip_y = hl[14].y
                p_tip_x, p_tip_y = hl[20].x, hl[20].y
                p_pip_y = hl[18].y
                
                # FIXED: Changed dots into underscores for the y variables
                t_i_dst = ((i_tip_x - t_tip_x)*fw)**2 + ((i_tip_y - t_tip_y)*fh)**2
                t_p_dst = ((p_tip_x - t_tip_x)*fw)**2 + ((p_tip_y - t_tip_y)*fh)**2
                
                # Adaptive reference calculations
                ref_length_sq = ((i_pip_x - i_mcp_x)*fw)**2 + ((i_pip_y - i_mcp_y)*fh)**2
                ref_length = max(1.0, ref_length_sq**0.5)
                normalized_pinch_distance = (t_i_dst**0.5) / ref_length
                
                is_i_o = i_tip_y < i_pip_y
                is_m_o = m_tip_y < m_pip_y
                is_r_c = r_tip_y > r_pip_y
                is_p_c = p_tip_y > p_pip_y 
                
                is_spidey = is_i_o and (not is_m_o) and is_r_c and (not is_p_c) and (t_p_dst > 2000) and (t_i_dst > 2000)
                is_scroll_swipe_mode = is_i_o and is_m_o and is_r_c and is_p_c and (t_i_dst > 2000)

                # --- 1. SLIDE SWIPE & HOLD AUTO-SCROLL BLOCK ---
                if is_scroll_swipe_mode:
                    left_cnt, right_cnt = max(0, left_cnt-2), max(0, right_cnt-2)
                    cx, cy = int(((i_tip_x + hl[8].x)/2)*fw), int(((i_tip_y + m_tip_y)/2)*fh)
                    
                    swipe_x_hist.append(cx)
                    if len(swipe_x_hist) > 5:
                        swipe_x_hist.pop(0)
                        dx = swipe_x_hist[-1] - swipe_x_hist[0]
                        c_t = time.time()
                        
                        if abs(dx) > 45 and (c_t - last_click_time) > 0.6:
                            key = win32con.VK_LEFT if dx < 0 else win32con.VK_RIGHT
                            win32api.keybd_event(key, 0, 0, 0)
                            win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
                            last_click_time = c_t
                            swipe_x_hist.clear()
                    
                    current_finger_y_normalized = (i_tip_y + m_tip_y) / 2
                    
                    if current_finger_y_normalized < (BOX_CENTER_Y - 0.05):
                        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, SCROLL_SPEED_MULTIPLIER, 0)
                    elif current_finger_y_normalized > (BOX_CENTER_Y + 0.05):
                        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -SCROLL_SPEED_MULTIPLIER, 0)
                        
                    cv2.circle(frame, (cx, cy), 8, (255, 255, 255), -1, cv2.LINE_AA)
                    
                # --- 2. BASE CURSOR TRACKING MODE ---
                else:
                    swipe_x_hist.clear()
                    nx, ny = max(0.0, min(1.0, (i_tip_x - min_x)/(max_x - min_x))), max(0.0, min(1.0, (i_tip_y - min_y)/(max_y - min_y)))
                    tx, ty = nx * screen_width, ny * screen_height
                    
                    if prev_x is None: smooth_x, smooth_y = tx, ty
                    else:
                        spd = ((tx - prev_x)**2 + (ty - prev_y)**2)**0.5
                        alpha = 0.30 if spd < 15 else (0.75 if spd > 45 else 0.50)
                        smooth_x = prev_x + alpha * (tx - prev_x)
                        smooth_y = prev_y + alpha * (ty - prev_y)
                    prev_x, prev_y = smooth_x, smooth_y
                    win32api.SetCursorPos((int(smooth_x), int(smooth_y)))
                    
                    is_pinch = normalized_pinch_distance < 0.65 and not is_spidey
                    c_t = time.time()
                    
                    if (c_t - last_click_time) > 0.22:
                        if is_pinch:
                            left_cnt += 1
                            if left_cnt >= 3:
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                last_click_time, left_cnt = c_t, 0
                        else: left_cnt = max(0, left_cnt - 1)
                        
                        if is_spidey:
                            right_cnt += 1
                            if right_cnt >= 5:
                                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                                last_click_time, right_cnt = c_t, 0
                        else: right_cnt = max(0, right_cnt - 1)
                    cv2.circle(frame, get_p(8), 5, (255, 255, 255), -1, cv2.LINE_AA)
                    
        mini_frame = cv2.resize(frame, (240, 180))
        cv2.imshow(win_name, mini_frame)
        
        if not window_reconfigured:
            hwnd = win32gui.FindWindow(None, win_name)
            if hwnd != 0:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 240, 180, win32con.SWP_SHOWWINDOW)
                window_reconfigured = True

        if cv2.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv2.destroyAllWindows()
