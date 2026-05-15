import mediapipe as mp
print(f"MediaPipe Version: {mp.__version__}")
try:
    print(f"Solutions: {mp.solutions}")
except AttributeError:
    print("AttributeError: mediapipe has no attribute 'solutions'")
    print(f"Dir(mp): {dir(mp)}")
