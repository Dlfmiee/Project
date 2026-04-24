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

class FireHandPro:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.8, 
            min_tracking_confidence=0.8
        )
        
        # Particle System State
        self.particles = []
        self.fire_active = False
        self.intensity = 0.0 # Used for smooth fade in/out
        
        # Audio Initialization
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                # PRO TIP: Save a sound as 'fire_whoosh.wav' and uncomment below
                # self.fire_sound = pygame.mixer.Sound("fire_whoosh.wav") 
                self.sound_playing = False
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.sound_playing = False
        else:
            self.sound_playing = False

    def get_fire_color(self, life):
        """Returns a BGR color based on particle life (1.0 to 0.0)."""
        if life > 0.8: return (220, 255, 255) # Intense White/Yellow
        if life > 0.4: return (0, 140, 255)   # Vibrant Orange
        if life > 0.1: return (0, 0, 180)     # Deep Red
        return (60, 60, 60)                   # Smoke Grey

    def update_particles(self, img, center):
        """Updates particle positions and draws them with alpha blending."""
        # Smoothly transition intensity
        target = 1.0 if self.fire_active else 0.0
        self.intensity += (target - self.intensity) * 0.15 
        
        overlay = img.copy()
        
        # Sound Control logic (Ready for user to uncomment Sound init)
        if hasattr(self, 'fire_sound'):
            if self.fire_active and not self.sound_playing:
                self.fire_sound.play(-1) # Loop
                self.sound_playing = True
            elif not self.fire_active and self.sound_playing:
                self.fire_sound.stop()
                self.sound_playing = False

        if self.intensity > 0.01:
            # Spawn new fire particles
            # More intensity = more particles
            num_spawns = int(20 * self.intensity)
            for _ in range(num_spawns):
                self.particles.append({
                    'pos': [
                        center[0] + random.randint(-25, 25), 
                        center[1] + random.randint(-15, 15)
                    ],
                    'vel': [
                        random.uniform(-2.0, 2.0), 
                        random.uniform(-8, -3) # Moving UP
                    ],
                    'life': 1.0,
                    'size': random.randint(4, 14)
                })

        # Update & Draw particles
        new_particles = []
        for p in self.particles:
            # Apply velocity
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            
            # Reduce life
            p['life'] -= 0.025
            
            if p['life'] > 0:
                color = self.get_fire_color(p['life'])
                # Size shrinks as life ends
                size = int(p['size'] * p['life'] * (1 + self.intensity))
                if size > 0:
                    cv2.circle(overlay, (int(p['pos'][0]), int(p['pos'][1])), size, color, -1)
                new_particles.append(p)
        
        self.particles = new_particles
        
        # Add a subtle "Glow" by blending the overlay
        # Higher intensity = more opacity
        alpha = 0.7 * self.intensity
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def process_frame(self, img):
        """Main processing loop for hand detection and effect triggering."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        
        if results.multi_hand_landmarks:
            hand_lms = results.multi_hand_landmarks[0]
            h, w, _ = img.shape
            
            # 1. Extract Landmark Positions
            lm_list = []
            for id, lm in enumerate(hand_lms.landmark):
                lm_list.append([int(lm.x * w), int(lm.y * h)])
            
            # 2. Gesture Detection (Counting Fingers)
            # Logic: If finger tip is higher than joint below it, it's UP
            fingers = []
            # Thumb (Horizontal comparison)
            if lm_list[4][0] > lm_list[3][0]: fingers.append(1)
            else: fingers.append(0)
            
            # 4 Fingers (Vertical comparison)
            for tip in [8, 12, 16, 20]:
                if lm_list[tip][1] < lm_list[tip-2][1]: fingers.append(1)
                else: fingers.append(0)
            
            # 3. Fire Logic: All 5 up = FIRE
            extended_count = sum(fingers)
            if extended_count == 5:
                self.fire_active = True
            elif extended_count <= 1: # Fist or just thumb
                self.fire_active = False
            
            # 4. Render Effect
            # Landmark 9 is the base of the middle finger (good center point)
            center = lm_list[9]
            self.update_particles(img, center)
            
            # 5. Dashboard UI
            status_color = (0, 215, 255) if self.fire_active else (150, 150, 150)
            # Semi-transparent background for text
            rect_overlay = img.copy()
            cv2.rectangle(rect_overlay, (20, 30), (280, 100), (0, 0, 0), -1)
            cv2.addWeighted(rect_overlay, 0.5, img, 0.5, 0, img)
            
            cv2.putText(img, "POWER STATUS", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(img, "MAX FIRE" if self.fire_active else "STBY", 
                        (40, 90), cv2.FONT_HERSHEY_TRIPLEX, 1.0, status_color, 2)

        return img

def main():
    # Attempt to open webcam
    cap = cv2.VideoCapture(0)
    
    # Set to HD for better quality if supported
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    app = FireHandPro()
    p_time = 0
    
    print("--- Fire Hand Pro Started ---")
    print("Instructions:")
    print("- Open hand (5 fingers) to trigger FIRE.")
    print("- Close fist to stop.")
    print("- Press 'q' to quit.")
    
    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read from webcam.")
            break
            
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
        cv2.imshow("Fire Hand Pro - v1.0", processed_frame)
        
        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Application closed.")

if __name__ == "__main__":
    main()
