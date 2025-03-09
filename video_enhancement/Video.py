import cv2
import numpy as np
import logging
import os
from typing import Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FrameMetrics:
    mean_brightness: float
    contrast: float
    histogram_spread: float
    frame_number: int

class VideoProcessor:
    def __init__(self, user_login: str = "bibhabasuiitkgp", timestamp: str = "2025-03-09 05:49:42"):
        self.logger = logging.getLogger(__name__)
        
        # Threshold values for brightness adjustment
        self.BRIGHTNESS_LOW_THRESHOLD = 80  # Below this is too dark
        self.BRIGHTNESS_HIGH_THRESHOLD = 200  # Above this is too bright
        self.TARGET_BRIGHTNESS = 127  # Ideal middle gray
        
        # Temporal smoothing parameters
        self.SMOOTHING_WINDOW = 5  # Number of frames for smoothing
        self.previous_adjustments = []
        
        # Watermark settings
        self.user_login = user_login
        self.timestamp = timestamp

    def analyze_frame(self, frame: np.ndarray, frame_number: int) -> FrameMetrics:
        """
        Analyze video frame and return key metrics for brightness/exposure assessment
        """
        # Convert to LAB color space for better brightness analysis
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Calculate metrics
        mean_brightness = np.mean(l_channel)
        contrast = np.std(l_channel)
        histogram_spread = np.percentile(l_channel, 95) - np.percentile(l_channel, 5)

        return FrameMetrics(
            mean_brightness=mean_brightness,
            contrast=contrast,
            histogram_spread=histogram_spread,
            frame_number=frame_number
        )

    def _get_smoothed_adjustment(self, current_adjustment: float) -> float:
        """
        Apply temporal smoothing to avoid sudden brightness changes
        """
        self.previous_adjustments.append(current_adjustment)
        if len(self.previous_adjustments) > self.SMOOTHING_WINDOW:
            self.previous_adjustments.pop(0)
        
        return np.mean(self.previous_adjustments)

    def _enhance_dark_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance dark frames using adaptive histogram equalization
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE with temporal consistency
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels and convert back to BGR
        enhanced_lab = cv2.merge([cl, a, b])
        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return enhanced_frame

    def _reduce_brightness(self, frame: np.ndarray, current_brightness: float) -> np.ndarray:
        """
        Reduce brightness for overexposed frames with temporal smoothing
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Calculate reduction factor with temporal smoothing
        reduction_factor = self.TARGET_BRIGHTNESS / current_brightness
        smoothed_factor = self._get_smoothed_adjustment(reduction_factor)

        # Adjust V channel (brightness)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * smoothed_factor, 0, 255).astype(np.uint8)

        # Convert back to BGR
        adjusted_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return adjusted_frame

    def _optimize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply subtle optimization for frames with acceptable brightness
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply gentle CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels and convert back
        enhanced_lab = cv2.merge([cl, a, b])
        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return enhanced_frame

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

    def process_video(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Process video file and adjust brightness/exposure frame by frame

        Args:
            input_path: Path to input video
            output_path: Path to save processed video

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Open video file
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False, "Failed to open video file"

            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            frame_count = 0
            self.previous_adjustments = []

            # Process frame by frame
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Get frame metrics
                metrics = self.analyze_frame(frame, frame_count)
                self.logger.info(f"Frame {frame_count}/{total_frames} - Brightness: {metrics.mean_brightness:.2f}")

                # Apply appropriate adjustment
                if metrics.mean_brightness < self.BRIGHTNESS_LOW_THRESHOLD:
                    processed_frame = self._enhance_dark_frame(frame)
                elif metrics.mean_brightness > self.BRIGHTNESS_HIGH_THRESHOLD:
                    processed_frame = self._reduce_brightness(frame, metrics.mean_brightness)
                else:
                    processed_frame = self._optimize_frame(frame)

                # Add Mansio watermark
                watermarked_frame = self.add_mansio_watermark(processed_frame)

                # Write processed frame
                out.write(watermarked_frame)
                frame_count += 1

                # Optional: Display progress
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"Processing: {progress:.1f}% complete")

            # Release resources
            cap.release()
            out.release()

            return True, f"Video processed successfully. Processed {frame_count} frames."

        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            return False, str(e)
        finally:
            # Ensure resources are released
            if 'cap' in locals():
                cap.release()
            if 'out' in locals():
                out.release()

def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Print to console
            logging.FileHandler("video_processing.log"),  # Save to file
        ],
    )
    return logging.getLogger(__name__)

def main():
    # Setup logging
    logger = setup_logging()

    # Initialize the VideoProcessor with specified timestamp and user
    processor = VideoProcessor(
        user_login="bibhabasuiitkgp",
        timestamp="2025-03-09 05:49:42"
    )

    # Define input video name and output video name
    input_video = "lowlight1.mp4"  # Place your video in the same directory with this name
    output_video = f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, input_video)
    output_path = os.path.join(current_dir, output_video)

    # Check if input video exists
    if not os.path.exists(input_path):
        logger.error(f"Input video not found: {input_path}")
        print(f"Please place a video named '{input_video}' in the same directory as this script.")
        return

    # Process the video
    logger.info(f"Processing video: {input_video}")
    print("Starting video processing. This may take a while depending on the video length...")
    
    success, message = processor.process_video(input_path, output_path)

    if success:
        logger.info("Video processing completed successfully")
        logger.info(f"Enhanced video saved as: {output_video}")
        print(f"\nSuccess! Enhanced video has been saved as '{output_video}'")
    else:
        logger.error(f"Video processing failed: {message}")
        print(f"\nError: {message}")

if __name__ == "__main__":
    main()