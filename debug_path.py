import mediapipe
print(f"MediaPipe File: {mediapipe.__file__}")
try:
    from mediapipe.solutions import hands
    print("Successfully imported mediapipe.solutions.hands")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
