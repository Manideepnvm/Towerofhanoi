import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Tuple, Any

class HandDetector:
    """
    Encapsulates MediaPipe Hands for detecting hand landmarks.
    """
    def __init__(self, 
                 max_num_hands: int = 1, 
                 min_detection_confidence: float = 0.5, 
                 min_tracking_confidence: float = 0.5) -> None:
        """
        Initialize the HandDetector.

        Args:
            max_num_hands (int): Maximum number of hands to detect.
            min_detection_confidence (float): Confidence threshold for detection.
            min_tracking_confidence (float): Confidence threshold for tracking.
        """
        self.mp_hands = mp.solutions.hands # type: ignore
        self.mp_drawing = mp.solutions.drawing_utils # type: ignore
        self.mp_drawing_styles = mp.solutions.drawing_styles # type: ignore
        
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence)
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[List[Tuple[int, int]]], np.ndarray]:
        """
        Process a video frame to detect hands and draw landmarks.

        Args:
            frame (np.ndarray): The BGR image frame from OpenCV.

        Returns:
            Tuple[Optional[List[Tuple[int, int]]], np.ndarray]: 
                - A list of (x, y) coordinates for [Index Tip, Thumb Tip, Wrist] if detected, else None.
                - The processed frame with landmarks drawn.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_landmarks_data: Optional[List[Tuple[int, int]]] = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on frame
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style())
                
                # Get dimensions
                h, w, _ = frame.shape
                
                # Extract key landmarks
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                
                # Convert to pixel coordinates
                index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
                thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
                
                # Store coordinates tuple: (index, thumb, wrist)
                hand_landmarks_data = [(index_x, index_y), (thumb_x, thumb_y), (wrist_x, wrist_y)]
                
                # We only process the primary hand
                break
                
        return hand_landmarks_data, frame
