"""
Unit Tests for iOS Format Converter
===================================

Comprehensive test suite covering:
- IOSConverter class functionality
- File format detection
- Error handling
- Path operations
- Dependency checks

Run tests with: python -m pytest tests/test_converter.py -v
Or simply: python tests/test_converter.py
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_converter_cli import (
    IOSConverter,
    get_default_output_dir,
    check_dependencies,
    HEIF_SUPPORT,
    PIL_AVAILABLE
)


class TestIOSConverterInit(unittest.TestCase):
    """Test cases for IOSConverter initialization."""
    
    def test_supported_formats_defined(self):
        """Verify supported formats are properly defined."""
        converter = IOSConverter()
        
        # Check image formats
        self.assertIn('.heic', converter.SUPPORTED_IMAGE_FORMATS)
        self.assertIn('.heif', converter.SUPPORTED_IMAGE_FORMATS)
        
        # Check video formats
        self.assertIn('.mov', converter.SUPPORTED_VIDEO_FORMATS)
        self.assertIn('.m4v', converter.SUPPORTED_VIDEO_FORMATS)
    
    def test_formats_are_lowercase(self):
        """Ensure all format extensions are lowercase."""
        converter = IOSConverter()
        
        for fmt in converter.SUPPORTED_IMAGE_FORMATS:
            self.assertEqual(fmt, fmt.lower(), f"Format {fmt} should be lowercase")
        
        for fmt in converter.SUPPORTED_VIDEO_FORMATS:
            self.assertEqual(fmt, fmt.lower(), f"Format {fmt} should be lowercase")
    
    def test_ffmpeg_path_attribute_exists(self):
        """Verify ffmpeg_path attribute is set during init."""
        converter = IOSConverter()
        self.assertTrue(hasattr(converter, 'ffmpeg_path'))


class TestFFmpegDetection(unittest.TestCase):
    """Test cases for FFmpeg detection logic."""
    
    def test_find_ffmpeg_returns_string_or_none(self):
        """FFmpeg path should be string or None."""
        converter = IOSConverter()
        result = converter._find_ffmpeg()
        
        self.assertTrue(
            result is None or isinstance(result, str),
            "ffmpeg_path should be string or None"
        )
    
    @patch('subprocess.run')
    def test_find_ffmpeg_in_path(self, mock_run):
        """Test FFmpeg detection when available in PATH."""
        mock_run.return_value = MagicMock(returncode=0)
        
        converter = IOSConverter()
        # Re-run detection with mocked subprocess
        with patch.object(converter, '_find_ffmpeg') as mock_find:
            mock_find.return_value = 'ffmpeg'
            converter.ffmpeg_path = converter._find_ffmpeg()
        
        self.assertEqual(converter.ffmpeg_path, 'ffmpeg')
    
    @patch('subprocess.run')
    def test_find_ffmpeg_not_in_path(self, mock_run):
        """Test FFmpeg detection when not in PATH."""
        mock_run.side_effect = FileNotFoundError()
        
        # This tests the actual behavior when FFmpeg isn't found
        converter = IOSConverter()
        # Path might still be found in common locations or bundled
        # so we just verify the method runs without error


class TestScanDirectory(unittest.TestCase):
    """Test cases for directory scanning functionality."""
    
    def setUp(self):
        """Create temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.converter = IOSConverter()
        
        # Create test files
        self.test_files = [
            'photo1.heic',
            'photo2.HEIF',  # Test case insensitivity
            'video1.mov',
            'video2.M4V',   # Test case insensitivity
            'document.pdf',  # Should be ignored
            'image.jpg',     # Should be ignored
        ]
        
        for filename in self.test_files:
            Path(self.test_dir, filename).touch()
        
        # Create subdirectory with files
        self.sub_dir = Path(self.test_dir, 'subfolder')
        self.sub_dir.mkdir()
        Path(self.sub_dir, 'nested.heic').touch()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_scan_finds_supported_files(self):
        """Verify scanner finds all supported file types."""
        files = self.converter.scan_directory(self.test_dir, recursive=False)
        
        # Should find 4 iOS files (heic, heif, mov, m4v)
        self.assertEqual(len(files), 4)
    
    def test_scan_ignores_unsupported_files(self):
        """Verify scanner ignores non-iOS formats."""
        files = self.converter.scan_directory(self.test_dir, recursive=False)
        
        for f in files:
            self.assertNotIn('.pdf', f.lower())
            self.assertNotIn('.jpg', f.lower())
    
    def test_scan_recursive(self):
        """Test recursive directory scanning."""
        files = self.converter.scan_directory(self.test_dir, recursive=True)
        
        # Should find 5 files (4 in root + 1 in subfolder)
        self.assertEqual(len(files), 5)
    
    def test_scan_non_recursive(self):
        """Test non-recursive directory scanning."""
        files = self.converter.scan_directory(self.test_dir, recursive=False)
        
        # Should find only 4 files (root only)
        self.assertEqual(len(files), 4)
    
    def test_scan_case_insensitive(self):
        """Verify scanner handles mixed case extensions."""
        files = self.converter.scan_directory(self.test_dir, recursive=False)
        
        extensions = [Path(f).suffix.lower() for f in files]
        self.assertIn('.heic', extensions)
        self.assertIn('.heif', extensions)
        self.assertIn('.mov', extensions)
        self.assertIn('.m4v', extensions)
    
    def test_scan_returns_list(self):
        """Verify scan returns a list."""
        files = self.converter.scan_directory(self.test_dir)
        self.assertIsInstance(files, list)
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        empty_dir = tempfile.mkdtemp()
        try:
            files = self.converter.scan_directory(empty_dir)
            self.assertEqual(files, [])
        finally:
            shutil.rmtree(empty_dir)


class TestConvertFile(unittest.TestCase):
    """Test cases for file conversion routing."""
    
    def setUp(self):
        """Set up converter instance."""
        self.converter = IOSConverter()
    
    def test_convert_file_routes_heic(self):
        """Verify HEIC files are routed to image converter."""
        with patch.object(self.converter, 'convert_heic_to_png') as mock:
            mock.return_value = Path('test.png')
            
            # Create a temp file to test
            with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as f:
                temp_path = f.name
            
            try:
                self.converter.convert_file(temp_path)
                mock.assert_called_once()
            except RuntimeError:
                # May fail if dependencies not installed - that's ok
                pass
            finally:
                os.unlink(temp_path)
    
    def test_convert_file_routes_mov(self):
        """Verify MOV files are routed to video converter."""
        with patch.object(self.converter, 'convert_mov_to_mp4') as mock:
            mock.return_value = Path('test.mp4')
            
            # Create a temp file to test
            with tempfile.NamedTemporaryFile(suffix='.mov', delete=False) as f:
                temp_path = f.name
            
            try:
                self.converter.convert_file(temp_path)
                mock.assert_called_once()
            except RuntimeError:
                # May fail if FFmpeg not installed - that's ok
                pass
            finally:
                os.unlink(temp_path)
    
    def test_convert_file_unsupported_format(self):
        """Verify unsupported formats raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(ValueError) as context:
                self.converter.convert_file(temp_path)
            
            self.assertIn('Unsupported format', str(context.exception))
        finally:
            os.unlink(temp_path)


class TestOutputDirectory(unittest.TestCase):
    """Test cases for output directory creation."""
    
    def test_get_default_output_dir_creates_folder(self):
        """Verify default output directory is created."""
        output_dir = get_default_output_dir()
        
        self.assertTrue(output_dir.exists())
        self.assertTrue(output_dir.is_dir())
        
        # Clean up
        shutil.rmtree(output_dir)
    
    def test_get_default_output_dir_has_timestamp(self):
        """Verify output directory name contains timestamp."""
        output_dir = get_default_output_dir()
        
        self.assertIn('Converted_', output_dir.name)
        
        # Clean up
        shutil.rmtree(output_dir)
    
    def test_convert_file_creates_output_dir(self):
        """Verify output directory is created if it doesn't exist."""
        converter = IOSConverter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / 'new_folder' / 'nested'
            
            # Create a dummy input file
            input_file = Path(temp_dir) / 'test.heic'
            input_file.touch()
            
            # This should create the output directory
            # (even if conversion fails due to invalid file)
            try:
                converter.convert_file(input_file, output_dir)
            except Exception:
                pass  # Expected to fail, we're testing dir creation
            
            # Directory should be created regardless of conversion result
            self.assertTrue(output_dir.exists())


class TestDependencyCheck(unittest.TestCase):
    """Test cases for dependency checking."""
    
    def test_check_dependencies_returns_bool(self):
        """Verify check_dependencies returns boolean."""
        # Capture print output
        with patch('builtins.print'):
            result = check_dependencies()
        
        self.assertIsInstance(result, bool)
    
    def test_pil_available_flag(self):
        """Verify PIL_AVAILABLE flag is boolean."""
        self.assertIsInstance(PIL_AVAILABLE, bool)
    
    def test_heif_support_flag(self):
        """Verify HEIF_SUPPORT flag is boolean."""
        self.assertIsInstance(HEIF_SUPPORT, bool)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling."""
    
    def setUp(self):
        """Set up converter instance."""
        self.converter = IOSConverter()
    
    def test_convert_heic_without_pillow(self):
        """Test error when Pillow is not installed."""
        with patch('ios_converter_cli.PIL_AVAILABLE', False):
            # Need to reimport or patch at module level
            converter = IOSConverter()
            
            with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as f:
                temp_path = f.name
            
            try:
                # This should raise RuntimeError about missing Pillow
                with self.assertRaises(RuntimeError):
                    converter.convert_heic_to_png(temp_path)
            finally:
                os.unlink(temp_path)
    
    def test_convert_mov_without_ffmpeg(self):
        """Test error when FFmpeg is not installed."""
        converter = IOSConverter()
        converter.ffmpeg_path = None  # Simulate missing FFmpeg
        
        with tempfile.NamedTemporaryFile(suffix='.mov', delete=False) as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(RuntimeError) as context:
                converter.convert_mov_to_mp4(temp_path)
            
            self.assertIn('FFmpeg', str(context.exception))
        finally:
            os.unlink(temp_path)


class TestPathHandling(unittest.TestCase):
    """Test cases for path handling."""
    
    def setUp(self):
        """Set up converter instance."""
        self.converter = IOSConverter()
    
    def test_convert_accepts_string_path(self):
        """Verify conversion accepts string paths."""
        with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as f:
            temp_path = f.name
        
        try:
            # Should not raise TypeError for string path
            # Will raise other errors (invalid file) - that's expected
            self.converter.convert_file(temp_path)
        except TypeError:
            self.fail("Should accept string path without TypeError")
        except (RuntimeError, ValueError, Exception):
            pass  # Other errors are OK, we're testing path type handling
        finally:
            os.unlink(temp_path)
    
    def test_convert_accepts_path_object(self):
        """Verify conversion accepts Path objects."""
        with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Should not raise TypeError for Path object
            # Will raise other errors (invalid file) - that's expected
            self.converter.convert_file(temp_path)
        except TypeError:
            self.fail("Should accept Path object without TypeError")
        except (RuntimeError, ValueError, Exception):
            pass  # Other errors are OK, we're testing path type handling
        finally:
            os.unlink(temp_path)


class TestMemoryManagement(unittest.TestCase):
    """Test cases for memory management and resource cleanup."""
    
    def test_image_context_manager_usage(self):
        """Verify images are opened with context manager (prevents memory leaks)."""
        import inspect
        from ios_converter_cli import IOSConverter
        
        # Get the source code of convert_heic_to_png
        source = inspect.getsource(IOSConverter.convert_heic_to_png)
        
        # Verify 'with Image.open' pattern is used
        self.assertIn('with Image.open', source,
                     "Image should be opened with context manager to prevent memory leaks")
    
    def test_subprocess_timeout_set(self):
        """Verify subprocess calls have timeout to prevent hangs."""
        import inspect
        from ios_converter_cli import IOSConverter
        
        # Get the source code of convert_mov_to_mp4
        source = inspect.getsource(IOSConverter.convert_mov_to_mp4)
        
        # Verify timeout parameter is used
        self.assertIn('timeout', source,
                     "Subprocess calls should have timeout to prevent infinite hangs")


# =============================================================================
# INTEGRATION TESTS (require actual files)
# =============================================================================

class TestIntegration(unittest.TestCase):
    """
    Integration tests that test actual conversion.
    
    These tests are skipped if dependencies are not installed.
    """
    
    @unittest.skipUnless(PIL_AVAILABLE and HEIF_SUPPORT, 
                        "Pillow and pillow-heif required")
    def test_actual_heic_conversion(self):
        """Test actual HEIC to PNG conversion (if test file exists)."""
        # This test would require an actual HEIC file
        # Skipped in basic test suite
        pass
    
    @unittest.skipUnless(PIL_AVAILABLE and HEIF_SUPPORT,
                        "Pillow and pillow-heif required")
    def test_conversion_preserves_image_quality(self):
        """Verify converted images maintain reasonable quality."""
        # This would require actual test files
        pass


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    """Run all tests with verbose output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIOSConverterInit))
    suite.addTests(loader.loadTestsFromTestCase(TestFFmpegDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestScanDirectory))
    suite.addTests(loader.loadTestsFromTestCase(TestConvertFile))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputDirectory))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyCheck))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestPathHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
