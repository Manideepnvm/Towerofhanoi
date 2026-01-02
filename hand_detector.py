import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence)
    
    def process_frame(self, frame):
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_landmarks_data = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on frame
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style())
                
                # Get specific landmarks
                h, w, _ = frame.shape
                
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                
                # Convert to pixel coordinates
                index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
                thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
                
                # Store coordinates tuple: (index, thumb, wrist)
                # Each is (x, y)
                hand_landmarks_data = [(index_x, index_y), (thumb_x, thumb_y), (wrist_x, wrist_y)]
                
                # We only process the first hand
                break
                
        return hand_landmarks_data, frame
