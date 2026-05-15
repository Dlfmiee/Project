import cv2
import mediapipe as mp
import time
import numpy as np
import random
try:
    import pygame # For premium sound effects
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Robust import fix for Windows AttributeErrors
try:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_drawing
except ImportError:
    import mediapipe.solutions.hands as mp_hands
    import mediapipe.solutions.drawing_utils as mp_drawing

class FireHandPro:
    def __init__(self):
        # Initialize MediaPipe
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )

        
        # Particle System State
        self.particles = []
        
        # Per-hand state: {hand_id: {'active': bool, 'intensity': float, 'prev_pos': [x,y], 'velocity': [x,y]}}
        self.hand_states = {}
        
        # Audio Initialization
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.sound_playing = False
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.sound_playing = False
        else:
            self.sound_playing = False

    def get_fire_color(self, life, p_type='fire'):
        """Returns a BGR color based on particle life and type."""
        if p_type == 'spark':
            return (150, 255, 255) if life > 0.5 else (0, 200, 255)
            
        if life > 0.8: return (200, 255, 255) # Intense White/Yellow
        if life > 0.4: return (0, 120, 255)   # Vibrant Orange
        if life > 0.1: return (0, 0, 180)     # Deep Red
        return (40, 40, 40)                   # Smoke Grey

    def update_particles(self, img, active_hands_info):
        """Updates particle positions and draws them with alpha blending."""
        overlay = img.copy()
        
        # 1. Spawn new particles for each active hand
        for hand_info in active_hands_info:
            center = hand_info['center']
            vel_inh = hand_info['velocity']
            intensity = hand_info['intensity']
            
            if intensity > 0.05:
                # Spawn fire particles
                num_spawns = int(25 * intensity)
                for _ in range(num_spawns):
                    self.particles.append({
                        'pos': [
                            center[0] + random.randint(-20, 20), 
                            center[1] + random.randint(-10, 10)
                        ],
                        'vel': [
                            random.uniform(-1.5, 1.5) - (vel_inh[0] * 0.2), 
                            random.uniform(-7, -3) - (vel_inh[1] * 0.2)
                        ],
                        'life': 1.0,
                        'size': random.randint(3, 12),
                        'type': 'fire'
                    })
                
                # Spawn Sparks
                if random.random() < 0.3 * intensity:
                    self.particles.append({
                        'pos': [center[0], center[1]],
                        'vel': [random.uniform(-5, 5), random.uniform(-10, -5)],
                        'life': 1.0,
                        'size': random.randint(1, 3),
                        'type': 'spark'
                    })

        # 2. Update & Draw all particles
        new_particles = []
        # Calculate max intensity for overall alpha blending
        intensities = [h['intensity'] for h in active_hands_info]
        max_intensity = max(intensities) if intensities else 0
        
        for p in self.particles:
            # Apply velocity + some "turbulence"
            p['pos'][0] += p['vel'][0] + random.uniform(-0.5, 0.5)
            p['pos'][1] += p['vel'][1]
            
            # Reduce life
            decay = 0.02 if p['type'] == 'spark' else 0.03
            p['life'] -= decay
            
            if p['life'] > 0:
                color = self.get_fire_color(p['life'], p['type'])
                # Size shrinks as life ends
                size = int(p['size'] * p['life'] * (1 + max_intensity))
                if size > 0:
                    cv2.circle(overlay, (int(p['pos'][0]), int(p['pos'][1])), size, color, -1)
                new_particles.append(p)
        
        self.particles = new_particles
        
        # 3. Blend Overlay
        alpha = min(0.8, 0.6 * max_intensity + 0.1) if max_intensity > 0 else 0
        if alpha > 0:
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def is_finger_up(self, lm_list, tip, base):
        """Robust check if finger is extended."""
        return lm_list[tip][1] < lm_list[base][1]

    def process_frame(self, img):
        """Main processing loop for multi-hand detection and effect triggering."""
        h, w, _ = img.shape
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        
        current_active_hands = []
        
        if results.multi_hand_landmarks:
            for i, hand_lms in enumerate(results.multi_hand_landmarks):
                # Extract Landmark Positions
                lm_list = []
                for lm in hand_lms.landmark:
                    lm_list.append([int(lm.x * w), int(lm.y * h)])
                
                # Robust Gesture Detection
                fingers = []
                # Thumb logic: Distance between thumb tip and pinky base
                # This is more robust than simple horizontal check
                thumb_dist = np.linalg.norm(np.array(lm_list[4]) - np.array(lm_list[17]))
                palm_size = np.linalg.norm(np.array(lm_list[0]) - np.array(lm_list[9]))
                if thumb_dist > palm_size * 0.8: fingers.append(1)
                else: fingers.append(0)
                
                for tip, base in [(8,6), (12,10), (16,14), (20,18)]:
                    fingers.append(1 if self.is_finger_up(lm_list, tip, base) else 0)
                
                # Fire Logic: 4 or more fingers up triggers fire
                extended_count = sum(fingers)
                is_active = extended_count >= 4
                
                # Tracking State
                hand_id = i
                if hand_id not in self.hand_states:
                    self.hand_states[hand_id] = {'intensity': 0.0, 'prev_pos': lm_list[9], 'velocity': [0, 0]}
                
                state = self.hand_states[hand_id]
                target_intensity = 1.0 if is_active else 0.0
                state['intensity'] += (target_intensity - state['intensity']) * 0.2
                
                # Calculate Velocity (for trailing effect)
                curr_pos = lm_list[9]
                state['velocity'] = [curr_pos[0] - state['prev_pos'][0], curr_pos[1] - state['prev_pos'][1]]
                state['prev_pos'] = curr_pos
                
                current_active_hands.append({
                    'center': curr_pos,
                    'intensity': state['intensity'],
                    'velocity': state['velocity']
                })

        # Update and Render
        self.update_particles(img, current_active_hands)
        
        # Dashboard UI
        any_active = any(h['intensity'] > 0.5 for h in current_active_hands)
        status_color = (0, 215, 255) if any_active else (150, 150, 150)
        
        rect_overlay = img.copy()
        cv2.rectangle(rect_overlay, (20, 30), (320, 100), (0, 0, 0), -1)
        cv2.addWeighted(rect_overlay, 0.5, img, 0.5, 0, img)
        
        cv2.putText(img, "FIRE HAND PRO v2.0", (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        status_text = "DUAL IGNITION" if len(current_active_hands) > 1 and any_active else ("MAX FIRE" if any_active else "STBY")
        cv2.putText(img, status_text, (40, 90), cv2.FONT_HERSHEY_TRIPLEX, 0.9, status_color, 2)

        return img

def main():
    # Try different indices in case 0 is not the right camera
    cap = None
    for idx in [0, 1, 2]:
        for backend in [None, cv2.CAP_DSHOW, cv2.CAP_MSMF]:
            backend_name = "Default" if backend is None else ("DSHOW" if backend == cv2.CAP_DSHOW else "MSMF")
            print(f"Attempting camera {idx} with {backend_name}...")
            
            if backend is None:
                temp_cap = cv2.VideoCapture(idx)
            else:
                temp_cap = cv2.VideoCapture(idx, backend)
                
            if temp_cap.isOpened():
                success, _ = temp_cap.read()
                if success:
                    cap = temp_cap
                    print(f"Successfully connected to camera {idx} using {backend_name}!")
                    break
            temp_cap.release()
        if cap: break
    
    if cap is None:
        print("ERROR: Could not find an active webcam. Please check your connections and permissions.")
        return
    
    # Use default resolution first for compatibility
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution: {int(actual_w)}x{int(actual_h)}")
    
    app = FireHandPro()
    p_time = 0
    
    print("--- Fire Hand Pro v2.0 Started ---")
    print("Instructions:")
    print("- Open hand (4-5 fingers) to trigger FIRE.")
    print("- Close fist to stop.")
    print("- Press 'q' to quit.")
    
    while True:
        try:
            success, frame = cap.read()
            if not success or frame is None:
                print("Warning: Failed to read from webcam. Retrying...")
                time.sleep(0.1)
                continue
            
            if frame.size == 0:
                continue
                
            frame = cv2.flip(frame, 1) # Mirror for natural feel
            
            # Core processing
            processed_frame = app.process_frame(frame)
            
            # Calculate FPS
            c_time = time.time()
            fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
            p_time = c_time
            cv2.putText(processed_frame, f"FPS: {int(fps)}", (1150, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display Result
            cv2.imshow("Fire Hand Pro - v2.0", processed_frame)
            
            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Application closed.")

if __name__ == "__main__":
    main()
