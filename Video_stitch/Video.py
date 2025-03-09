import cv2
import numpy as np
import logging
import os
from typing import List, Tuple, Optional
from datetime import datetime

class VideoStitcher:
    def __init__(self, user_login: str = "bibhabasuiitkgp"):
        self.logger = logging.getLogger(__name__)
        self.TRANSITION_FRAMES = 30  # Number of frames for fade transition
        self.OUTPUT_FPS = 30  # Standard output FPS
        self.DEFAULT_WIDTH = 1920  # Default output width
        self.DEFAULT_HEIGHT = 1080  # Default output height
        self.user_login = user_login
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def process_videos(  # Changed method name from stitch_videos to process_videos
        self,
        video_paths: List[str],
        output_path: str,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Stitch multiple videos together with fade transitions and Mansio watermark"""
        try:
            if not video_paths:
                return False, "No video paths provided"

            target_width = target_width or self.DEFAULT_WIDTH
            target_height = target_height or self.DEFAULT_HEIGHT

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(
                output_path, fourcc, self.OUTPUT_FPS, (target_width, target_height)
            )

            last_frame = None
            total_videos = len(video_paths)

            for video_index, video_path in enumerate(video_paths):
                self.logger.info(
                    f"Processing video {video_index + 1}/{total_videos}: {video_path}"
                )

                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.logger.error(f"Could not open video: {video_path}")
                    continue

                frame_count = 0
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    resized_frame = self.resize_frame(frame, target_width, target_height)

                    if last_frame is not None and frame_count == 0:
                        transition_frames = self.create_fade_transition(
                            last_frame, resized_frame, self.TRANSITION_FRAMES
                        )
                        for trans_frame in transition_frames:
                            watermarked_trans = self.add_mansio_watermark(trans_frame)
                            out.write(watermarked_trans)

                    watermarked_frame = self.add_mansio_watermark(resized_frame)
                    out.write(watermarked_frame)
                    last_frame = resized_frame.copy()
                    frame_count += 1

                    if frame_count % 30 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(
                            f"Video {video_index + 1}/{total_videos}: {progress:.1f}% complete"
                        )

                cap.release()

            out.release()
            return True, "Videos stitched successfully with Mansio watermark"

        except Exception as e:
            self.logger.error(f"Error stitching videos: {str(e)}")
            return False, str(e)
        finally:
            if "cap" in locals():
                cap.release()
            if "out" in locals():
                out.release()

    def resize_frame(self, frame: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
        """Resize frame while maintaining aspect ratio and adding black bars if needed"""
        if frame is None:
            return None

        frame_aspect = frame.shape[1] / frame.shape[0]
        target_aspect = target_width / target_height

        if frame_aspect > target_aspect:
            new_width = target_width
            new_height = int(target_width / frame_aspect)
            top_padding = (target_height - new_height) // 2
            bottom_padding = target_height - new_height - top_padding
            left_padding = 0
            right_padding = 0
        else:
            new_height = target_height
            new_width = int(target_height * frame_aspect)
            left_padding = (target_width - new_width) // 2
            right_padding = target_width - new_width - left_padding
            top_padding = 0
            bottom_padding = 0

        resized = cv2.resize(frame, (new_width, new_height))
        padded = cv2.copyMakeBorder(
            resized,
            top_padding,
            bottom_padding,
            left_padding,
            right_padding,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0],
        )

        return padded

    def create_fade_transition(self, frame1: np.ndarray, frame2: np.ndarray, num_frames: int) -> List[np.ndarray]:
        """Create a smooth fade transition between two frames"""
        transition_frames = []
        for i in range(num_frames):
            alpha = i / num_frames
            blended = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
            transition_frames.append(blended)
        return transition_frames

    def add_mansio_watermark(self, frame: np.ndarray) -> np.ndarray:
        """Add Mansio watermark with timestamp and user info"""
        output = frame.copy()
        
        # Main watermark text
        main_text = "Mansio"
        timestamp_text = f"UTC: {self.timestamp}"
        user_text = f"Created by: {self.user_login}"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        main_font_scale = 1.5
        info_font_scale = 0.6
        main_thickness = 3
        info_thickness = 2
        color = (255, 255, 255)  # White
        padding = 20
        line_spacing = 5
        
        # Calculate text sizes
        (main_width, main_height), _ = cv2.getTextSize(
            main_text, font, main_font_scale, main_thickness
        )
        (time_width, time_height), _ = cv2.getTextSize(
            timestamp_text, font, info_font_scale, info_thickness
        )
        (user_width, user_height), _ = cv2.getTextSize(
            user_text, font, info_font_scale, info_thickness
        )
        
        # Calculate positions
        total_height = main_height + time_height + user_height + 2 * line_spacing
        max_width = max(main_width, time_width, user_width)
        
        x = frame.shape[1] - max_width - 2 * padding
        y_bottom = frame.shape[0] - padding
        
        # Create semi-transparent background
        overlay = output.copy()
        cv2.rectangle(
            overlay,
            (x - padding, y_bottom - total_height - 2 * padding),
            (x + max_width + padding, y_bottom + padding),
            (0, 0, 0),
            -1
        )
        
        # Apply transparency
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
        
        # Add text
        y_main = y_bottom - user_height - time_height - 2 * line_spacing
        y_time = y_bottom - user_height - line_spacing
        y_user = y_bottom
        
        # Draw text
        cv2.putText(
            output, main_text, (x, y_main),
            font, main_font_scale, color, main_thickness, cv2.LINE_AA
        )
        cv2.putText(
            output, timestamp_text, (x, y_time),
            font, info_font_scale, color, info_thickness, cv2.LINE_AA
        )
        cv2.putText(
            output, user_text, (x, y_user),
            font, info_font_scale, color, info_thickness, cv2.LINE_AA
        )
        
        return output