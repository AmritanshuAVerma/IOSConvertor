"""
iOS Format Converter - Command Line Version
============================================

A command-line tool to convert iOS media formats to more common formats:
- HEIC/HEIF images -> PNG
- MOV/M4V videos -> MP4

Author: iOS Converter Project
License: MIT
Version: 1.0.0

Dependencies:
    - Pillow: Image processing library
    - pillow-heif: HEIC/HEIF format support for Pillow
    - FFmpeg: Video conversion (bundled or system-installed)

Usage:
    python ios_converter_cli.py photo.heic           # Convert single file
    python ios_converter_cli.py -d /path/to/folder   # Convert folder
    python ios_converter_cli.py --check              # Check dependencies
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# =============================================================================
# DEPENDENCY INITIALIZATION
# =============================================================================

# Try to import pillow-heif for HEIC support
# This must be done before importing PIL.Image to register the HEIF opener
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

# Import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# =============================================================================
# CONVERTER CLASS
# =============================================================================

class IOSConverter:
    """
    Main converter class for iOS media formats.
    
    Handles conversion of:
    - HEIC/HEIF images to PNG format
    - MOV/M4V videos to MP4 format (H.264 + AAC)
    
    Attributes:
        SUPPORTED_IMAGE_FORMATS (list): List of supported image extensions
        SUPPORTED_VIDEO_FORMATS (list): List of supported video extensions
        ffmpeg_path (str|None): Path to FFmpeg executable, None if not found
    
    Example:
        >>> converter = IOSConverter()
        >>> converter.convert_file('photo.heic', '/output/dir')
        PosixPath('/output/dir/photo.png')
    """
    
    # Supported file extensions (lowercase)
    SUPPORTED_IMAGE_FORMATS: List[str] = ['.heic', '.heif']
    SUPPORTED_VIDEO_FORMATS: List[str] = ['.mov', '.m4v']
    
    def __init__(self) -> None:
        """
        Initialize the converter and locate FFmpeg.
        
        FFmpeg search order:
        1. Bundled with PyInstaller executable
        2. Local ffmpeg_bin folder (development)
        3. System PATH
        4. Common installation directories
        """
        self.ffmpeg_path: Optional[str] = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """
        Find the FFmpeg executable.
        
        Searches multiple locations to find FFmpeg, prioritizing bundled
        versions for portability.
        
        Returns:
            str: Path to FFmpeg executable if found
            None: If FFmpeg is not available
        
        Search Order:
            1. Bundled with PyInstaller exe (MEIPASS temp folder)
            2. Same directory as executable
            3. Local ffmpeg_bin folder (for development)
            4. System PATH
            5. Common Windows installation paths
        """
        # Check if running as bundled exe (PyInstaller sets 'frozen' attribute)
        if getattr(sys, 'frozen', False):
            # PyInstaller extracts to a temp folder accessed via _MEIPASS
            if hasattr(sys, '_MEIPASS'):
                bundled_ffmpeg = Path(sys._MEIPASS) / 'ffmpeg.exe'
                if bundled_ffmpeg.exists():
                    return str(bundled_ffmpeg)
            
            # Also check same directory as the exe
            exe_dir = Path(sys.executable).parent
            bundled_ffmpeg = exe_dir / 'ffmpeg.exe'
            if bundled_ffmpeg.exists():
                return str(bundled_ffmpeg)
        
        # Check in script directory (for development)
        try:
            script_dir = Path(__file__).parent
            local_ffmpeg = script_dir / 'ffmpeg_bin' / 'ffmpeg.exe'
            if local_ffmpeg.exists():
                return str(local_ffmpeg)
        except NameError:
            # __file__ may not exist in frozen exe
            pass
        
        # Check if ffmpeg is in system PATH
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10  # Prevent hanging
            )
            if result.returncode == 0:
                return 'ffmpeg'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check common Windows installation paths
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def convert_heic_to_png(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None
    ) -> Path:
        """
        Convert a HEIC/HEIF image to PNG format.
        
        Uses Pillow with pillow-heif extension to read HEIC files and
        save them as PNG. Preserves transparency if present.
        
        Args:
            input_path: Path to the input HEIC/HEIF file
            output_path: Optional output path. If None, uses input path
                        with .png extension
        
        Returns:
            Path: Path to the created PNG file
        
        Raises:
            RuntimeError: If Pillow or pillow-heif is not installed
            FileNotFoundError: If input file doesn't exist
            PIL.UnidentifiedImageError: If file is not a valid image
        
        Example:
            >>> converter = IOSConverter()
            >>> result = converter.convert_heic_to_png('photo.heic')
            >>> print(result)
            PosixPath('photo.png')
        """
        # Validate dependencies
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow is not installed. Run: pip install Pillow")
        
        if not HEIF_SUPPORT:
            raise RuntimeError("pillow-heif is not installed. Run: pip install pillow-heif")
        
        # Normalize paths
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.with_suffix('.png')
        else:
            output_path = Path(output_path)
        
        print(f"Converting: {input_path.name} -> {output_path.name}")
        
        # Open image using context manager to ensure proper cleanup
        # This prevents memory leaks by ensuring the image is closed
        with Image.open(input_path) as img:
            # Check if image has transparency (alpha channel)
            # RGBA: RGB with Alpha, LA: Grayscale with Alpha, P: Palette mode
            has_transparency = (
                img.mode in ('RGBA', 'LA') or
                (img.mode == 'P' and 'transparency' in img.info)
            )
            
            if has_transparency:
                # Keep transparency for PNG output
                img.save(output_path, 'PNG')
            else:
                # Convert to RGB (removes any alpha channel issues)
                # This also handles unusual color modes like CMYK
                img.convert('RGB').save(output_path, 'PNG')
        
        print(f"✓ Completed: {output_path.name}")
        return output_path
    
    def convert_mov_to_mp4(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None
    ) -> Path:
        """
        Convert a MOV/M4V video to MP4 format.
        
        Uses FFmpeg to re-encode the video with H.264 video codec and
        AAC audio codec for maximum compatibility.
        
        Args:
            input_path: Path to the input MOV/M4V file
            output_path: Optional output path. If None, uses input path
                        with .mp4 extension
        
        Returns:
            Path: Path to the created MP4 file
        
        Raises:
            RuntimeError: If FFmpeg is not installed or conversion fails
            FileNotFoundError: If input file doesn't exist
        
        FFmpeg Settings:
            - Video: H.264 (libx264), CRF 23, medium preset
            - Audio: AAC, 128kbps
            - Flags: faststart (enables streaming)
        
        Example:
            >>> converter = IOSConverter()
            >>> result = converter.convert_mov_to_mp4('video.mov')
            >>> print(result)
            PosixPath('video.mp4')
        """
        # Validate FFmpeg availability
        if not self.ffmpeg_path:
            raise RuntimeError(
                "FFmpeg is not installed or not found in PATH.\n"
                "Please install FFmpeg from https://ffmpeg.org/download.html"
            )
        
        # Normalize paths
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.with_suffix('.mp4')
        else:
            output_path = Path(output_path)
        
        print(f"Converting: {input_path.name} -> {output_path.name}")
        
        # Build FFmpeg command with optimized settings
        cmd = [
            self.ffmpeg_path,
            '-i', str(input_path),      # Input file
            '-c:v', 'libx264',          # Video codec: H.264
            '-preset', 'medium',         # Encoding speed/quality balance
            '-crf', '23',                # Constant Rate Factor (18-28 is good)
            '-c:a', 'aac',               # Audio codec: AAC
            '-b:a', '128k',              # Audio bitrate: 128 kbps
            '-movflags', '+faststart',   # Enable progressive download/streaming
            '-y',                        # Overwrite output without asking
            str(output_path)
        ]
        
        try:
            # Run FFmpeg with captured output
            # Using timeout to prevent infinite hangs on corrupted files
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for large files
            )
            
            if result.returncode != 0:
                # FFmpeg failed - extract error message
                error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Unknown error"
                raise RuntimeError(f"FFmpeg error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out (exceeded 1 hour)")
        except FileNotFoundError:
            raise RuntimeError(f"FFmpeg not found at: {self.ffmpeg_path}")
        
        print(f"✓ Completed: {output_path.name}")
        return output_path
    
    def convert_file(
        self,
        input_path: str | Path,
        output_dir: Optional[str | Path] = None
    ) -> Path:
        """
        Convert a single file based on its extension.
        
        Automatically detects the file type and routes to the appropriate
        conversion method.
        
        Args:
            input_path: Path to the input file
            output_dir: Optional output directory. If None, uses the same
                       directory as the input file
        
        Returns:
            Path: Path to the converted output file
        
        Raises:
            ValueError: If the file format is not supported
            RuntimeError: If conversion fails
        
        Example:
            >>> converter = IOSConverter()
            >>> converter.convert_file('photo.heic', '/output')
            PosixPath('/output/photo.png')
        """
        input_path = Path(input_path)
        ext = input_path.suffix.lower()
        
        # Setup output directory
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_path.parent
        
        # Route to appropriate converter based on extension
        if ext in self.SUPPORTED_IMAGE_FORMATS:
            output_path = output_dir / (input_path.stem + '.png')
            return self.convert_heic_to_png(input_path, output_path)
        elif ext in self.SUPPORTED_VIDEO_FORMATS:
            output_path = output_dir / (input_path.stem + '.mp4')
            return self.convert_mov_to_mp4(input_path, output_path)
        else:
            supported = self.SUPPORTED_IMAGE_FORMATS + self.SUPPORTED_VIDEO_FORMATS
            raise ValueError(
                f"Unsupported format: {ext}\n"
                f"Supported formats: {', '.join(supported)}"
            )
    
    def scan_directory(
        self,
        directory: str | Path,
        recursive: bool = True
    ) -> List[str]:
        """
        Scan a directory for supported iOS media files.
        
        Args:
            directory: Path to the directory to scan
            recursive: If True, scan subdirectories recursively
        
        Returns:
            list: List of absolute paths to supported files
        
        Example:
            >>> converter = IOSConverter()
            >>> files = converter.scan_directory('/photos', recursive=True)
            >>> print(files)
            ['/photos/img1.heic', '/photos/sub/img2.heif']
        """
        directory = Path(directory)
        supported_exts = self.SUPPORTED_IMAGE_FORMATS + self.SUPPORTED_VIDEO_FORMATS
        files: List[str] = []
        
        if recursive:
            # Walk through all subdirectories
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if Path(filename).suffix.lower() in supported_exts:
                        files.append(os.path.join(root, filename))
        else:
            # Only scan immediate directory
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in supported_exts:
                    files.append(str(item))
        
        return files


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_output_dir() -> Path:
    """
    Create a dated output folder in the executable/script directory.
    
    Creates a folder named 'Converted_YYYY-MM-DD_HH-MM-SS' for organizing
    converted files.
    
    Returns:
        Path: Path to the created output directory
    
    Example:
        >>> output_dir = get_default_output_dir()
        >>> print(output_dir)
        PosixPath('/app/Converted_2026-01-19_14-30-45')
    """
    # Determine base directory (handles both script and frozen exe)
    if getattr(sys, 'frozen', False):
        # For frozen exe, use the directory where the exe is located
        base_dir = Path(sys.executable).parent
    else:
        try:
            base_dir = Path(__file__).parent
        except NameError:
            base_dir = Path.cwd()
    
    # Create timestamped folder name
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = base_dir / f"Converted_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def check_dependencies() -> bool:
    """
    Check and report the status of all required dependencies.
    
    Checks for:
    - Pillow (image processing)
    - pillow-heif (HEIC/HEIF support)
    - FFmpeg (video conversion)
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    
    Example:
        >>> if check_dependencies():
        ...     print("Ready to convert!")
    """
    print("Checking dependencies...")
    all_ok = True
    
    # Check Pillow
    if PIL_AVAILABLE:
        print("  ✓ Pillow is installed")
    else:
        print("  ✗ Pillow is NOT installed (pip install Pillow)")
        all_ok = False
    
    # Check pillow-heif
    if HEIF_SUPPORT:
        print("  ✓ pillow-heif is installed")
    else:
        print("  ✗ pillow-heif is NOT installed (pip install pillow-heif)")
        all_ok = False
    
    # Check FFmpeg
    converter = IOSConverter()
    if converter.ffmpeg_path:
        print(f"  ✓ FFmpeg found: {converter.ffmpeg_path}")
    else:
        print("  ✗ FFmpeg is NOT installed (needed for video conversion)")
        all_ok = False
    
    print()
    return all_ok


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> None:
    """
    Main entry point for the command-line interface.
    
    Parses command-line arguments and orchestrates the conversion process.
    Supports individual file conversion, directory scanning, and batch processing.
    """
    # Setup argument parser with examples
    parser = argparse.ArgumentParser(
        description='Convert iOS formats (HEIC/HEIF, MOV) to PNG and MP4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s photo.heic                    Convert single file
  %(prog)s *.heic                        Convert all HEIC files
  %(prog)s -d ~/Photos                   Convert all files in directory
  %(prog)s -d ~/Photos -o ~/Converted    Convert with output directory
  %(prog)s --check                       Check dependencies
        """
    )
    
    # Define command-line arguments
    parser.add_argument(
        'files',
        nargs='*',
        help='Files to convert (supports wildcards)'
    )
    parser.add_argument(
        '-d', '--directory',
        help='Directory to scan for iOS media files'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: dated folder in app directory)'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='Scan directories recursively (default: True)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check dependencies and exit'
    )
    
    args = parser.parse_args()
    
    # Handle --check flag
    if args.check:
        check_dependencies()
        return
    
    # Validate input
    if not args.files and not args.directory:
        parser.print_help()
        print("\nNo files or directory specified. Use --check to verify dependencies.")
        return
    
    # Check dependencies (warn but continue)
    if not check_dependencies():
        print("Warning: Some dependencies are missing. Conversion may fail.")
        print()
    
    # Initialize converter
    converter = IOSConverter()
    files_to_convert: List[str] = list(args.files) if args.files else []
    
    # Add files from directory scan
    if args.directory:
        if os.path.isdir(args.directory):
            found_files = converter.scan_directory(args.directory, args.recursive)
            files_to_convert.extend(found_files)
            print(f"Found {len(found_files)} file(s) in {args.directory}")
        else:
            print(f"Error: Directory not found: {args.directory}")
            return
    
    # Check if we have files to convert
    if not files_to_convert:
        print("No supported files found.")
        return
    
    # Setup output directory (dated folder by default)
    output_dir = args.output if args.output else get_default_output_dir()
    print(f"\nOutput folder: {output_dir}")
    print(f"Converting {len(files_to_convert)} file(s)...")
    print("=" * 50)
    
    # Process files with error tracking
    success = 0
    failed = 0
    
    for file_path in files_to_convert:
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"✗ File not found: {file_path}")
            failed += 1
            continue
        
        try:
            converter.convert_file(file_path, output_dir)
            success += 1
        except Exception as e:
            print(f"✗ Error: {Path(file_path).name} - {str(e)}")
            failed += 1
    
    # Print summary
    print("=" * 50)
    print(f"Completed: {success} succeeded, {failed} failed")
    print(f"Output saved to: {output_dir}")


if __name__ == "__main__":
    main()
