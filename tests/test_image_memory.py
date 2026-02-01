"""
Tests for ImageMemory

Test image metadata storage and retrieval.
"""

import pytest
import tempfile
import json
from pathlib import Path
from alpha.multimodal.image_memory import ImageMemory, ImageRecord


@pytest.fixture
def temp_db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_image_memory.db"
        yield str(db_path)


@pytest.fixture
def image_memory(temp_db):
    """Create ImageMemory instance"""
    memory = ImageMemory(db_path=temp_db)
    yield memory
    memory.close()


class TestImageMemory:
    """Test ImageMemory"""

    def test_initialize_database(self, temp_db):
        """Test database initialization"""
        memory = ImageMemory(db_path=temp_db)

        assert memory.conn is not None
        assert Path(temp_db).exists()

        memory.close()

    def test_calculate_content_hash(self, image_memory):
        """Test content hash calculation"""
        data1 = b"image data 1"
        data2 = b"image data 2"

        hash1 = image_memory.calculate_content_hash(data1)
        hash2 = image_memory.calculate_content_hash(data2)

        assert hash1 != hash2
        assert len(hash1) == 64  # SHA256 hex digest

        # Same data should produce same hash
        hash1_again = image_memory.calculate_content_hash(data1)
        assert hash1 == hash1_again

    def test_store_image(self, image_memory):
        """Test storing image metadata"""
        metadata = {
            "file_path": "/path/to/image.png",
            "format": "PNG",
            "size_bytes": 1024,
            "width": 800,
            "height": 600
        }

        analysis = {
            "description": "A test image",
            "confidence": 0.95
        }

        result = image_memory.store_image(
            image_id="img_001",
            image_hash="abc123def456",
            metadata=metadata,
            analysis_result=analysis,
            conversation_id="conv_001"
        )

        assert result is True

    def test_store_duplicate_image(self, image_memory):
        """Test storing duplicate image (same hash)"""
        metadata = {
            "file_path": "/path/to/image.png",
            "format": "PNG",
            "size_bytes": 1024,
            "width": 800,
            "height": 600
        }

        # Store first time
        image_memory.store_image(
            image_id="img_001",
            image_hash="duplicate_hash",
            metadata=metadata
        )

        # Try to store again with same hash
        result = image_memory.store_image(
            image_id="img_002",
            image_hash="duplicate_hash",
            metadata=metadata
        )

        assert result is False  # Should reject duplicate

    def test_get_by_hash(self, image_memory):
        """Test retrieving image by hash"""
        metadata = {
            "file_path": "/path/to/image.png",
            "format": "PNG",
            "size_bytes": 1024,
            "width": 800,
            "height": 600
        }

        image_memory.store_image(
            image_id="img_001",
            image_hash="find_me_hash",
            metadata=metadata
        )

        record = image_memory.get_by_hash("find_me_hash")

        assert record is not None
        assert record.id == "img_001"
        assert record.hash == "find_me_hash"
        assert record.format == "PNG"
        assert record.width == 800

    def test_get_by_hash_not_found(self, image_memory):
        """Test retrieving non-existent hash"""
        record = image_memory.get_by_hash("nonexistent_hash")

        assert record is None

    def test_get_by_id(self, image_memory):
        """Test retrieving image by ID"""
        metadata = {
            "file_path": "/path/to/image.png",
            "format": "PNG",
            "size_bytes": 1024,
            "width": 800,
            "height": 600
        }

        image_memory.store_image(
            image_id="img_find_me",
            image_hash="some_hash",
            metadata=metadata
        )

        record = image_memory.get_by_id("img_find_me")

        assert record is not None
        assert record.id == "img_find_me"
        assert record.hash == "some_hash"

    def test_get_recent(self, image_memory):
        """Test getting recent images"""
        # Store multiple images
        for i in range(5):
            metadata = {
                "file_path": f"/path/to/image{i}.png",
                "format": "PNG",
                "size_bytes": 1024 * i,
                "width": 800,
                "height": 600
            }
            image_memory.store_image(
                image_id=f"img_{i:03d}",
                image_hash=f"hash_{i}",
                metadata=metadata
            )

        recent = image_memory.get_recent(limit=3)

        assert len(recent) == 3
        # Verify all returned records are valid
        for record in recent:
            assert record.id.startswith("img_")
            assert record.format == "PNG"

    def test_get_recent_by_conversation(self, image_memory):
        """Test getting recent images for specific conversation"""
        # Store images in different conversations
        for i in range(3):
            metadata = {"file_path": f"/path/to/image{i}.png", "format": "PNG"}
            image_memory.store_image(
                image_id=f"img_{i}",
                image_hash=f"hash_{i}",
                metadata=metadata,
                conversation_id="conv_A"
            )

        for i in range(3, 6):
            metadata = {"file_path": f"/path/to/image{i}.png", "format": "PNG"}
            image_memory.store_image(
                image_id=f"img_{i}",
                image_hash=f"hash_{i}",
                metadata=metadata,
                conversation_id="conv_B"
            )

        # Get images for conv_A only
        recent = image_memory.get_recent(conversation_id="conv_A")

        assert len(recent) == 3
        for record in recent:
            assert record.conversation_id == "conv_A"

    def test_search_by_format(self, image_memory):
        """Test searching images by format"""
        # Store images with different formats
        for i, fmt in enumerate(["PNG", "PNG", "JPEG", "GIF"]):
            metadata = {"file_path": f"/path/to/image{i}.{fmt.lower()}", "format": fmt}
            image_memory.store_image(
                image_id=f"img_{i}",
                image_hash=f"hash_{i}",
                metadata=metadata
            )

        # Search for PNG images
        png_images = image_memory.search_by_format("PNG")

        assert len(png_images) == 2
        for record in png_images:
            assert record.format == "PNG"

    def test_get_statistics(self, image_memory):
        """Test getting statistics"""
        # Store images with different formats
        for i in range(5):
            fmt = "PNG" if i < 3 else "JPEG"
            metadata = {
                "file_path": f"/path/to/image{i}.{fmt.lower()}",
                "format": fmt,
                "size_bytes": 1024 * (i + 1)
            }
            image_memory.store_image(
                image_id=f"img_{i}",
                image_hash=f"hash_{i}",
                metadata=metadata
            )

        stats = image_memory.get_statistics()

        assert stats["total_images"] == 5
        assert stats["formats"]["PNG"] == 3
        assert stats["formats"]["JPEG"] == 2
        assert stats["total_size_bytes"] == 1024 * (1+2+3+4+5)
        assert stats["recent_7_days"] == 5

    def test_clear_old_records(self, image_memory):
        """Test clearing old records"""
        # Store some images
        for i in range(3):
            metadata = {"file_path": f"/path/to/image{i}.png", "format": "PNG"}
            image_memory.store_image(
                image_id=f"img_{i}",
                image_hash=f"hash_{i}",
                metadata=metadata
            )

        # Manually set old timestamp for one record
        cursor = image_memory.conn.cursor()
        cursor.execute("""
            UPDATE image_history
            SET analyzed_at = datetime('now', '-40 days')
            WHERE id = 'img_0'
        """)
        image_memory.conn.commit()

        # Clear records older than 30 days
        deleted = image_memory.clear_old_records(days=30)

        assert deleted == 1

        # Verify img_0 was deleted
        assert image_memory.get_by_id("img_0") is None
        assert image_memory.get_by_id("img_1") is not None

    def test_context_manager(self, temp_db):
        """Test using ImageMemory as context manager"""
        with ImageMemory(db_path=temp_db) as memory:
            metadata = {"file_path": "/path/to/image.png", "format": "PNG"}
            memory.store_image(
                image_id="img_001",
                image_hash="test_hash",
                metadata=metadata
            )

        # Connection should be closed after exiting context
        assert memory.conn is None

    def test_analysis_result_json(self, image_memory):
        """Test storing and retrieving analysis result as JSON"""
        metadata = {"file_path": "/path/to/image.png", "format": "PNG"}

        analysis = {
            "description": "A beautiful sunset",
            "objects": ["sky", "sun", "clouds"],
            "confidence": 0.98
        }

        image_memory.store_image(
            image_id="img_001",
            image_hash="test_hash",
            metadata=metadata,
            analysis_result=analysis
        )

        record = image_memory.get_by_id("img_001")

        # Parse JSON and verify
        stored_analysis = json.loads(record.analysis_result)
        assert stored_analysis["description"] == "A beautiful sunset"
        assert len(stored_analysis["objects"]) == 3
        assert stored_analysis["confidence"] == 0.98

    def test_image_record_to_dict(self):
        """Test ImageRecord to_dict method"""
        record = ImageRecord(
            id="img_001",
            file_path="/path/to/image.png",
            hash="abc123",
            format="PNG",
            width=800,
            height=600
        )

        data = record.to_dict()

        assert data["id"] == "img_001"
        assert data["file_path"] == "/path/to/image.png"
        assert data["width"] == 800

    def test_image_record_from_dict(self):
        """Test ImageRecord from_dict method"""
        data = {
            "id": "img_001",
            "file_path": "/path/to/image.png",
            "hash": "abc123",
            "format": "PNG",
            "size_bytes": 1024,
            "width": 800,
            "height": 600,
            "analyzed_at": "2026-02-01 14:00:00",
            "analysis_result": "{}",
            "conversation_id": "conv_001",
            "url": None
        }

        record = ImageRecord.from_dict(data)

        assert record.id == "img_001"
        assert record.format == "PNG"
        assert record.width == 800
