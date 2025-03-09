import cv2
import numpy as np
from PIL import Image
import logging
import os
from typing import Tuple, Optional
from dataclasses import dataclass


# First, include the ImageMetrics and ImageProcessor classes you provided
@dataclass
class ImageMetrics:
    mean_brightness: float
    contrast: float
    histogram_spread: float


class ImageProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Threshold values for brightness adjustment
        self.BRIGHTNESS_LOW_THRESHOLD = 80  # Below this is too dark
        self.BRIGHTNESS_HIGH_THRESHOLD = 130  # Above this is too bright
        self.TARGET_BRIGHTNESS = 127  # Ideal middle gray

    def analyze_image(self, image: np.ndarray) -> ImageMetrics:
        """
        Analyze image and return key metrics for brightness/exposure assessment
        """
        # Convert to LAB color space for better brightness analysis
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0] # L channel represents brightness in LAB color space

        # Calculate metrics
        mean_brightness = np.mean(l_channel)
        contrast = np.std(l_channel)
        histogram_spread = np.percentile(l_channel, 95) - np.percentile(l_channel, 5)

        return ImageMetrics(
            mean_brightness=mean_brightness,
            contrast=contrast,
            histogram_spread=histogram_spread,
        )

    def adjust_brightness(self, image_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Automatically detect and adjust image brightness/exposure

        Args:
            image_path: Path to input image
            output_path: Path to save processed image

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return False, "Failed to read image"

            # Get initial metrics
            metrics = self.analyze_image(img)
            self.logger.info(f"Initial metrics: {metrics}")

            # Determine if adjustment is needed
            if metrics.mean_brightness < self.BRIGHTNESS_LOW_THRESHOLD:
                # Image is too dark - apply adaptive histogram equalization
                self.logger.info("Image is too dark, applying brightness enhancement")
                processed_img = self._enhance_dark_image(img)

            elif metrics.mean_brightness > self.BRIGHTNESS_HIGH_THRESHOLD:
                # Image is too bright - reduce brightness
                self.logger.info("Image is too bright, reducing brightness")
                processed_img = self._reduce_brightness(img)

            else:
                # Image is within acceptable range - apply subtle optimization
                self.logger.info(
                    "Image brightness is acceptable, applying subtle optimization"
                )
                processed_img = self._optimize_image(img)

            # Verify improvement
            final_metrics = self.analyze_image(processed_img)
            self.logger.info(f"Final metrics: {final_metrics}")

            # Save processed image
            cv2.imwrite(output_path, processed_img)

            return True, "Image processed successfully"

        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            return False, str(e)

    def _enhance_dark_image(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance dark images using adaptive histogram equalization
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels and convert back to BGR
        enhanced_lab = cv2.merge([cl, a, b])
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return enhanced_img

    def _reduce_brightness(self, img: np.ndarray) -> np.ndarray:
        """
        Reduce brightness for overexposed images
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Calculate reduction factor based on current brightness
        current_brightness = np.mean(hsv[:, :, 2])
        reduction_factor = self.TARGET_BRIGHTNESS / current_brightness  # Adjust to target brightness

        # Adjust V channel (brightness)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * reduction_factor, 0, 255).astype(np.uint8)

        # Convert back to BGR
        adjusted_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return adjusted_img

    def _optimize_image(self, img: np.ndarray) -> np.ndarray:
        """
        Apply subtle optimization for images with acceptable brightness
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply gentle CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge channels and convert back
        enhanced_lab = cv2.merge([cl, a, b])
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return enhanced_img


def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Print to console
            logging.FileHandler("image_processing.log"),  # Save to file
        ],
    )
    return logging.getLogger(__name__)


def main():
    # Setup logging
    logger = setup_logging()

    # Initialize the ImageProcessor
    processor = ImageProcessor()

    # Define input image name and output image name
    input_image = "18.png"  # Place your image in the same directory with this name
    output_image = "enhanced_" + input_image

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, input_image)
    output_path = os.path.join(current_dir, output_image)

    # Check if input image exists
    if not os.path.exists(input_path):
        logger.error(f"Input image not found: {input_path}")
        print(
            f"Please place an image named '{input_image}' in the same directory as this script."
        )
        return

    # Process the image
    logger.info(f"Processing image: {input_image}")
    success, message = processor.adjust_brightness(input_path, output_path)

    if success:
        logger.info(f"Image processing completed successfully")
        logger.info(f"Enhanced image saved as: {output_image}")
        print(f"\nSuccess! Enhanced image has been saved as '{output_image}'")
    else:
        logger.error(f"Image processing failed: {message}")
        print(f"\nError: {message}")


if __name__ == "__main__":
    main()
