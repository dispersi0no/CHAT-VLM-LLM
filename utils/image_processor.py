"""Image preprocessing utilities."""

from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


class ImageProcessor:
    """Image preprocessing for OCR optimization."""

    @staticmethod
    def preprocess(
        image: Image.Image,
        resize: bool = True,
        max_dimension: int = 2048,
        enhance: bool = True,
        denoise: bool = False,
    ) -> Image.Image:
        """
        Preprocess image for optimal OCR results.

        Args:
            image: Input PIL Image
            resize: Whether to resize large images
            max_dimension: Maximum dimension for resizing
            enhance: Whether to enhance contrast and sharpness
            denoise: Whether to apply denoising

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large
        if resize:
            image = ImageProcessor.resize_if_needed(image, max_dimension)

        # Enhance image quality
        if enhance:
            image = ImageProcessor.enhance_image(image)

        # Denoise if requested
        if denoise:
            image = ImageProcessor.denoise(image)

        return image

    @staticmethod
    def resize_if_needed(image: Image.Image, max_dimension: int) -> Image.Image:
        """Resize image if any dimension exceeds max_dimension."""
        width, height = image.size

        if width <= max_dimension and height <= max_dimension:
            return image

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def enhance_image(image: Image.Image) -> Image.Image:
        """Enhance image contrast and sharpness."""
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        return image

    @staticmethod
    def denoise(image: Image.Image) -> Image.Image:
        """Apply denoising to reduce image noise."""
        # Convert to numpy array
        img_array = np.array(image)

        # Apply bilateral filter for noise reduction
        denoised = cv2.bilateralFilter(img_array, 9, 75, 75)

        # Convert back to PIL
        return Image.fromarray(denoised)

    @staticmethod
    def deskew(image: Image.Image) -> Image.Image:
        """Deskew tilted document images."""
        # Convert to numpy array
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is not None:
            # Calculate average angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)

            median_angle = np.median(angles)

            # Rotate image
            if abs(median_angle) > 0.5:  # Only rotate if angle is significant
                height, width = img_array.shape[:2]
                center = (width // 2, height // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    img_array,
                    rotation_matrix,
                    (width, height),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                return Image.fromarray(rotated)

        return image

    @staticmethod
    def crop_borders(image: Image.Image, threshold: int = 240) -> Image.Image:
        """Crop white borders from document images."""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Find non-white pixels
        mask = gray < threshold
        coords = np.argwhere(mask)

        if len(coords) == 0:
            return image

        # Get bounding box
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0)

        # Add small margin
        margin = 10
        y0 = max(0, y0 - margin)
        x0 = max(0, x0 - margin)
        y1 = min(img_array.shape[0], y1 + margin)
        x1 = min(img_array.shape[1], x1 + margin)

        # Crop image
        cropped = img_array[y0:y1, x0:x1]
        return Image.fromarray(cropped)

    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """Get image metadata and statistics."""
        return {
            "size": image.size,
            "mode": image.mode,
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "megapixels": round((image.width * image.height) / 1_000_000, 2),
        }
