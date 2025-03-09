import numpy as np
import cv2
import logging
from typing import Tuple
import os


class ImageProcessor:
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the exposure correction system.

        Args:
            debug_mode (bool): If True, enables debugging visualizations
        """
        self.debug_mode = debug_mode
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for the exposure correction process."""
        logging.basicConfig(
            level=logging.INFO, 
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def analyze_exposure(self, image: np.ndarray) -> Tuple[float, float, float]:
        """
        Analyze image exposure characteristics.
        """
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            avg_brightness = np.mean(gray)
            overexposed = np.sum(gray >= 250) / gray.size
            underexposed = np.sum(gray <= 5) / gray.size

            if self.debug_mode:
                self.logger.info(f"Average brightness: {avg_brightness:.2f}")
                self.logger.info(f"Overexposed ratio: {overexposed:.3f}")
                self.logger.info(f"Underexposed ratio: {underexposed:.3f}")

            return avg_brightness, overexposed, underexposed
        except Exception as e:
            self.logger.error(f"Error in analyze_exposure: {str(e)}")
            raise

    def apply_local_exposure_correction(
        self, image: np.ndarray, block_size: int = 16
    ) -> np.ndarray:
        """
        Apply local exposure correction using adaptive processing.
        """
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(block_size, block_size))
            corrected_l = clahe.apply(l)

            corrected_lab = cv2.merge([corrected_l, a, b])
            return cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)
        except Exception as e:
            self.logger.error(f"Error in apply_local_exposure_correction: {str(e)}")
            raise

    def correct_exposure(self, image: np.ndarray) -> np.ndarray:
        """
        Main method to correct image exposure.
        """
        try:
            if image is None or image.size == 0:
                raise ValueError("Invalid input image")

            corrected = image.copy()
            corrected = self.apply_local_exposure_correction(corrected)
            
            avg_brightness, _, _ = self.analyze_exposure(corrected)
            
            # Fine-tune brightness if needed
            if avg_brightness < 100:
                corrected = cv2.convertScaleAbs(corrected, alpha=1.2, beta=10)
            elif avg_brightness > 200:
                corrected = cv2.convertScaleAbs(corrected, alpha=0.8, beta=-10)

            return corrected
        except Exception as e:
            self.logger.error(f"Error in correct_exposure: {str(e)}")
            raise

    def adjust_brightness(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Process an image file and save the enhanced version.
        
        Args:
            input_path: Path to the input image
            output_path: Path where the processed image should be saved
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Read the image
            image = cv2.imread(input_path)
            if image is None:
                return False, "Failed to load input image"

            # Process the image
            enhanced_image = self.correct_exposure(image)

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save the processed image
            success = cv2.imwrite(output_path, enhanced_image)
            if not success:
                return False, "Failed to save enhanced image"

            return True, "Image enhanced successfully"

        except Exception as e:
            self.logger.error(f"Error in adjust_brightness: {str(e)}")
            return False, f"Error processing image: {str(e)}"