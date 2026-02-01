"""
Tests for ImageProcessor
"""

import io
import pytest
from pathlib import Path
from PIL import Image

from alpha.multimodal.image_processor import ImageProcessor, ImageValidationError


@pytest.fixture
def processor():
    """Create ImageProcessor instance"""
    return ImageProcessor()


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image"""
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def large_image(tmp_path):
    """Create a large test image"""
    img_path = tmp_path / "large.png"
    img = Image.new("RGB", (2000, 2000), color="blue")
    img.save(img_path)
    return img_path


class TestImageProcessor:
    """Test ImageProcessor class"""

    def test_load_image_success(self, processor, sample_image):
        """Test successful image loading"""
        image = processor.load_image(sample_image)

        assert isinstance(image, Image.Image)
        assert image.format == "PNG"
        assert image.width == 100
        assert image.height == 100

    def test_load_image_not_found(self, processor):
        """Test loading non-existent image"""
        with pytest.raises(ImageValidationError, match="not found"):
            processor.load_image("/nonexistent/image.png")

    def test_load_image_too_large(self, processor, tmp_path):
        """Test loading image exceeding size limit"""
        # Create a file larger than MAX_FILE_SIZE
        large_file = tmp_path / "too_large.png"
        with open(large_file, "wb") as f:
            f.write(b"0" * (ImageProcessor.MAX_FILE_SIZE + 1))

        with pytest.raises(ImageValidationError, match="too large"):
            processor.load_image(large_file)

    def test_load_corrupted_image(self, processor, tmp_path):
        """Test loading corrupted image file"""
        corrupted = tmp_path / "corrupted.png"
        with open(corrupted, "wb") as f:
            f.write(b"not a valid image")

        with pytest.raises(ImageValidationError, match="Failed to load"):
            processor.load_image(corrupted)

    def test_validate_image_success(self, processor, sample_image):
        """Test image validation success"""
        image = processor.load_image(sample_image)
        # Should not raise
        processor.validate_image(image)

    def test_validate_image_too_large_dimensions(self, processor):
        """Test validation with oversized dimensions"""
        img = Image.new("RGB", (5000, 5000))

        with pytest.raises(ImageValidationError, match="dimensions too large"):
            processor.validate_image(img)

    def test_optimize_image_no_optimization_needed(self, processor, sample_image):
        """Test optimization when image is already small"""
        image = processor.load_image(sample_image)
        optimized = processor.optimize_image(image)

        # Should return same image
        assert optimized.width == image.width
        assert optimized.height == image.height

    def test_optimize_image_reduces_size(self, processor, tmp_path):
        """Test optimization reduces image size"""
        # Create an image with random noise to ensure it's actually large
        import numpy as np

        # Create 2000x2000 image with random pixels (will compress poorly)
        img_path = tmp_path / "large_noisy.png"
        random_data = np.random.randint(0, 256, (2000, 2000, 3), dtype=np.uint8)
        img = Image.fromarray(random_data, 'RGB')
        img.save(img_path)

        image = processor.load_image(img_path)
        original_width = image.width
        original_height = image.height

        # Optimize with very low threshold to force scaling
        optimized = processor.optimize_image(image, max_size=50 * 1024)

        # Should be smaller
        assert optimized.width < original_width
        assert optimized.height < original_height

    def test_calculate_hash(self, processor, sample_image):
        """Test content hash calculation"""
        image = processor.load_image(sample_image)
        hash1 = processor.calculate_hash(image)

        # Hash should be consistent
        hash2 = processor.calculate_hash(image)
        assert hash1 == hash2

        # Hash should be valid SHA256 (64 hex chars)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_calculate_hash_different_images(self, processor, tmp_path):
        """Test different images have different hashes"""
        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"

        img1 = Image.new("RGB", (50, 50), color="red")
        img2 = Image.new("RGB", (50, 50), color="blue")

        img1.save(img1_path)
        img2.save(img2_path)

        image1 = processor.load_image(img1_path)
        image2 = processor.load_image(img2_path)

        hash1 = processor.calculate_hash(image1)
        hash2 = processor.calculate_hash(image2)

        assert hash1 != hash2

    def test_get_metadata(self, processor, sample_image):
        """Test metadata extraction"""
        image = processor.load_image(sample_image)
        metadata = processor.get_metadata(image, sample_image)

        assert metadata["format"] == "PNG"
        assert metadata["width"] == 100
        assert metadata["height"] == 100
        assert "size_kb" in metadata
        assert metadata["filename"] == "test.png"

    def test_get_metadata_without_file_path(self, processor, sample_image):
        """Test metadata extraction without file path"""
        image = processor.load_image(sample_image)
        metadata = processor.get_metadata(image)

        assert metadata["format"] == "PNG"
        assert metadata["width"] == 100
        assert metadata["height"] == 100
        assert metadata["size_kb"] is None

    def test_convert_format_png_to_jpeg(self, processor, sample_image):
        """Test format conversion PNG to JPEG"""
        image = processor.load_image(sample_image)
        converted = processor.convert_format(image, "JPEG")

        assert isinstance(converted, Image.Image)
        # Mode should be RGB for JPEG
        assert converted.mode == "RGB"

    def test_convert_format_unsupported(self, processor, sample_image):
        """Test conversion to unsupported format"""
        image = processor.load_image(sample_image)

        with pytest.raises(ImageValidationError, match="Unsupported target format"):
            processor.convert_format(image, "TIFF")

    def test_process_image_complete_pipeline(self, processor, sample_image):
        """Test complete image processing pipeline"""
        image, metadata = processor.process_image(sample_image)

        assert isinstance(image, Image.Image)
        assert "content_hash" in metadata
        assert metadata["width"] == 100
        assert metadata["height"] == 100

    def test_process_image_with_optimization(self, processor, large_image):
        """Test processing with optimization"""
        image, metadata = processor.process_image(large_image, optimize=True)

        assert isinstance(image, Image.Image)
        assert "content_hash" in metadata

    def test_process_image_with_format_conversion(self, processor, sample_image):
        """Test processing with format conversion"""
        image, metadata = processor.process_image(
            sample_image, target_format="JPEG"
        )

        assert isinstance(image, Image.Image)
        assert image.mode == "RGB"
