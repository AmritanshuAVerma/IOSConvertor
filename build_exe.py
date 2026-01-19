"""
Build script to create standalone executable with bundled FFmpeg
"""
import subprocess
import sys
import os

def build():
    # Check if ffmpeg exists
    ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg_bin', 'ffmpeg.exe')
    if not os.path.exists(ffmpeg_path):
        print("ERROR: ffmpeg.exe not found in ffmpeg_bin folder!")
        print("Please download FFmpeg and place ffmpeg.exe in the ffmpeg_bin folder.")
        return
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # Single executable
        '--name', 'iOSConverter',       # Output name
        '--console',                    # Console app (shows output)
        '--clean',                      # Clean build
        '--add-binary', 'ffmpeg_bin/ffmpeg.exe;.',  # Bundle FFmpeg
        'ios_converter_cli.py'
    ]
    
    print("Building standalone executable with bundled FFmpeg...")
    print("This may take a few minutes...\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("SUCCESS! Executable created at:")
        print("  dist/iOSConverter.exe")
        print("=" * 50)
        print("\nThis is a fully self-contained executable.")
        print("No dependencies need to be installed on target systems!")
    else:
        print("\nBuild failed!")
        
if __name__ == "__main__":
    build()
