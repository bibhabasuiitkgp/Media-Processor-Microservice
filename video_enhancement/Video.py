import numpy as np
import cv2
from typing import Tuple
import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from Image_Enhancement.Image import ImageProcessor

class VideoProcessor(ImageProcessor):
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the video processing system.
        Inherits from ImageProcessor for frame-by-frame processing.
        """
        super().__init__(debug_mode)
        self.processing_status = {}

    def get_video_info(self, video_path: str) -> Tuple[int, int, int, float]:
        """
        Get video metadata.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            return frame_count, width, height, fps
        except Exception as e:
            self.logger.error(f"Error getting video info: {str(e)}")
            raise

    def add_watermark(self, frame: np.ndarray) -> np.ndarray:
        """
        Add Mansio watermark with timestamp and user info to a frame.
        Creates a professional-looking overlay with proper formatting and positioning.
        """
        try:
            height, width = frame.shape[:2]
            
            # Fixed timestamp and user info
            timestamp = "2025-03-09 21:51:48"  # Use the fixed timestamp
            user = "bibhabasuiitkgp"
            
            # Create a more structured watermark with proper spacing
            watermark_text = [
                "MANSIO",  # Brand name in caps
                f"Processed: {timestamp} UTC",  # Timestamp
                f"User: {user}"  # User info
            ]
            
            # Text settings
            font = cv2.FONT_HERSHEY_SIMPLEX
            base_font_scale = min(width, height) / 1500.0
            
            # Different sizes for different lines
            font_scales = [
                base_font_scale * 1.2,  # Larger for brand name
                base_font_scale * 0.9,  # Smaller for timestamp
                base_font_scale * 0.9   # Smaller for user info
            ]
            
            # Calculate total height and maximum width
            total_height = 0
            max_width = 0
            text_sizes = []
            
            for text, scale in zip(watermark_text, font_scales):
                thickness = max(1, int(scale * 2))
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, font, scale, thickness
                )
                text_sizes.append((text_width, text_height, thickness, baseline))
                total_height += text_height + baseline + 5  # 5 pixels spacing
                max_width = max(max_width, text_width)

            # Position the watermark block
            padding = 20
            margin = 10
            block_width = max_width + 2 * padding
            block_height = total_height + 2 * padding
            
            # Create position for the entire block (bottom-right corner)
            block_x = width - block_width - margin
            block_y = height - margin - block_height

            # Create semi-transparent background
            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (block_x, block_y),
                (block_x + block_width, block_y + block_height),
                (0, 0, 0),
                -1
            )
            
            # Apply the overlay with transparency
            alpha = 0.7
            frame = cv2.addWeighted(overlay, 1-alpha, frame, alpha, 0)

            # Add text lines
            current_y = block_y + padding
            for i, (text, font_scale) in enumerate(zip(watermark_text, font_scales)):
                text_width, text_height, thickness, baseline = text_sizes[i]
                
                # Center text horizontally in the block
                text_x = block_x + (block_width - text_width) // 2
                
                # Add text with white color
                cv2.putText(
                    frame,
                    text,
                    (text_x, current_y + text_height),
                    font,
                    font_scale,
                    (255, 255, 255),  # White color
                    thickness,
                    cv2.LINE_AA
                )
                
                current_y += text_height + baseline + 5

            # Add a subtle border around the block
            cv2.rectangle(
                frame,
                (block_x, block_y),
                (block_x + block_width, block_y + block_height),
                (255, 255, 255),  # White border
                1,  # Thickness
                cv2.LINE_AA
            )
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error adding watermark: {str(e)}")
            return frame

    def process_frame_chunk(self, frames: list, start_idx: int) -> list:
        """
        Process a chunk of frames in parallel.
        """
        processed_frames = []
        for i, frame in enumerate(frames):
            try:
                processed_frame = self.correct_exposure(frame)
                processed_frame = self.add_watermark(processed_frame)
                processed_frames.append(processed_frame)
                
                if self.debug_mode and i % 10 == 0:
                    self.logger.info(f"Processed frame {start_idx + i}")
                    
            except Exception as e:
                self.logger.error(f"Error processing frame {start_idx + i}: {str(e)}")
                processed_frames.append(frame)
                
        return processed_frames

    def adjust_video_brightness(
        self, 
        input_path: str, 
        output_path: str,
        max_workers: int = 4,
        chunk_size: int = 30
    ) -> Tuple[bool, str]:
        """
        Process a video file and save the enhanced version.
        """
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False, "Failed to open input video"

            frame_count, width, height, fps = self.get_video_info(input_path)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                output_path, 
                fourcc, 
                fps, 
                (width, height)
            )

            frames_buffer = []
            processed_count = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                with tqdm(total=frame_count, desc="Processing video") as pbar:
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        frames_buffer.append(frame)
                        
                        if len(frames_buffer) >= chunk_size:
                            processed_frames = self.process_frame_chunk(
                                frames_buffer, 
                                processed_count
                            )
                            
                            for processed_frame in processed_frames:
                                out.write(processed_frame)
                            
                            processed_count += len(frames_buffer)
                            pbar.update(len(frames_buffer))
                            frames_buffer = []

                    if frames_buffer:
                        processed_frames = self.process_frame_chunk(
                            frames_buffer, 
                            processed_count
                        )
                        for processed_frame in processed_frames:
                            out.write(processed_frame)
                        
                        processed_count += len(frames_buffer)
                        pbar.update(len(frames_buffer))

            cap.release()
            out.release()
            
            return True, "Video enhanced successfully"

        except Exception as e:
            self.logger.error(f"Error in adjust_video_brightness: {str(e)}")
            return False, f"Error processing video: {str(e)}"