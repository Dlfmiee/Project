# 🔥 Steps to "Wow" Your Friends

Follow these steps to get the absolute best experience with your new Fire Hand superpower!

### 1. 🛠️ Installation
Before running the code, ensure all necessary libraries are installed:
```bash
pip install -r requirements.txt
```

### 2. 🔊 Add Sound Effects
The code has built-in logic for sound, but you need to provide the audio file:
1.  Find a "Fire Flame" or "Magic Whoosh" sound effect online (in `.wav` or `.mp3` format).
2.  Save it as `fire_whoosh.wav` in the same folder as your script.
3.  In `fire_hand.py`, look for these lines and remove the `#` to uncomment them:
    ```python
    # self.fire_sound = pygame.mixer.Sound("fire_whoosh.wav") 
    # self.fire_sound.play(-1)
    # self.fire_sound.stop()
    ```

### 3. 💡 Optimize Your Environment
*   **Lighting:** MediaPipe works best in a well-lit room. Avoid having a bright window directly behind you, as it makes your hand look like a dark silhouette.
*   **Background:** A plain background helps the hand tracking stay stable.
*   **Smoothing:** If the fire "flickers" too much, try to keep your hand steady or move it slightly closer to the camera.

### 4. 🖥️ Immersive Mode
*   **Fullscreen:** Once the window opens, press the **Maximize** button or double-click the title bar. 
*   **Dark Mode:** If you can, dim the lights in your room. The glowing fire particles will look much more vibrant and realistic!

### 5. 🎮 Controls
*   **Open Hand (5 fingers):** Triggers the FIRE effect!
*   **Closed Fist:** Extinguishes the fire.
*   **'Q' Key:** Press this to exit the application.
