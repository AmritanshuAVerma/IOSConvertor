# iOS Format Converter

A self-contained application to convert iOS media formats to more common formats:
- **HEIC/HEIF** images → **PNG**
- **MOV/M4V** videos → **MP4**

## 🚀 Quick Start (Standalone Executable)

**No installation required!** Just download and run:

1. Download `iOSConverter.exe` from the `dist` folder
2. Double-click to run, or use from command line:

```bash
# Check if everything works
iOSConverter.exe --check

# Convert a single file
iOSConverter.exe photo.heic

# Convert all files in a folder
iOSConverter.exe -d "C:\iPhone Photos"

# Drag and drop files onto the exe to convert them!
```

The standalone executable includes all dependencies (Python, Pillow, pillow-heif, FFmpeg) - nothing else needs to be installed!

---

## 📦 Features

- 🖼️ **HEIC/HEIF to PNG** - Convert iPhone photos to universal PNG format
- 🎬 **MOV/M4V to MP4** - Convert iPhone videos with H.264 codec
- 📁 **Batch conversion** - Convert multiple files at once
- 📂 **Folder scanning** - Auto-detect iOS files in directories (recursive)
- 📅 **Dated output folders** - Organized output in timestamped folders
- 💾 **Self-contained EXE** - No dependencies required on target system
- ⌨️ **Command-line interface** - Easy automation and scripting

---

## 🛠️ Installation (For Development)

If you want to run from source or modify the code:

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

```bash
# Clone or download the project
cd IosToJpg

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| Pillow | Image processing |
| pillow-heif | HEIC/HEIF format support |
| FFmpeg | Video conversion (bundled in `ffmpeg_bin/`) |

---

## 📖 Usage

### Standalone Executable

```bash
# Basic usage
iOSConverter.exe [options] [files...]

# Examples
iOSConverter.exe --check                    # Verify dependencies
iOSConverter.exe photo.heic                 # Convert single file
iOSConverter.exe *.heic                     # Convert all HEIC files
iOSConverter.exe -d "C:\Photos"             # Convert folder
iOSConverter.exe -d "C:\Photos" -o "C:\Out" # Custom output directory
```

### Python Script

```bash
# Run from source
python ios_converter_cli.py --check
python ios_converter_cli.py photo.heic
python ios_converter_cli.py -d /path/to/photos
```

### Batch File (convert.bat)

Double-click `convert.bat` for an interactive menu:

```
==========================================
       iOS Format Converter
  HEIC/HEIF to PNG  -  MOV/M4V to MP4
==========================================

  1. Check dependencies
  2. Launch GUI
  3. Select folder to convert
  4. Exit
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `files...` | Files to convert (supports wildcards) |
| `-d, --directory` | Directory to scan for iOS files |
| `-o, --output` | Output directory (default: dated folder) |
| `-r, --recursive` | Scan directories recursively (default: True) |
| `--check` | Check dependencies and exit |
| `-h, --help` | Show help message |

---

## 📋 Supported Formats

### Input Formats
| Extension | Type | Source |
|-----------|------|--------|
| `.heic` | Image | iPhone photos (iOS 11+) |
| `.heif` | Image | iPhone photos |
| `.mov` | Video | iPhone videos |
| `.m4v` | Video | iPhone videos |

### Output Formats
| Input | Output | Details |
|-------|--------|---------|
| HEIC/HEIF | PNG | Lossless, preserves transparency |
| MOV/M4V | MP4 | H.264 video + AAC audio |

---

## 🎬 Video Conversion Settings

Videos are converted using optimized FFmpeg settings:

| Setting | Value | Description |
|---------|-------|-------------|
| Video Codec | H.264 (libx264) | Universal compatibility |
| Quality | CRF 23 | Good quality/size balance |
| Preset | Medium | Balanced encoding speed |
| Audio Codec | AAC | Standard audio format |
| Audio Bitrate | 128 kbps | Good quality audio |
| Fast Start | Enabled | Web streaming support |

---

## 📁 Output Organization

Converted files are saved to dated folders by default:

```
IosToJpg/
├── Converted_2026-01-19_14-30-45/
│   ├── photo1.png
│   ├── photo2.png
│   └── video1.mp4
├── Converted_2026-01-19_15-00-00/
│   └── ...
└── iOSConverter.exe
```

Use `-o` to specify a custom output directory.

---

## 🏗️ Building the Executable

To build a new standalone executable:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Build executable (includes FFmpeg)
python build_exe.py
```

The executable will be created at `dist/iOSConverter.exe` (~50MB, includes all dependencies).

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_converter.py -v

# Or run directly
python tests/test_converter.py
```

Test coverage includes:
- ✅ Format detection
- ✅ Directory scanning
- ✅ Path handling
- ✅ Error handling
- ✅ Memory leak prevention
- ✅ Dependency checking

---

## ❗ Troubleshooting

### "pillow-heif not installed"
```bash
pip install pillow-heif
```

### "FFmpeg not found"
The standalone executable includes FFmpeg. If running from source:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Place `ffmpeg.exe` in the `ffmpeg_bin/` folder

### "Conversion failed" for videos
- Ensure the input file is not corrupted
- Check available disk space
- Try converting a smaller file first

### Antivirus blocking the executable
Some antivirus software may flag PyInstaller executables. This is a false positive - the executable is safe. You can:
1. Add an exception in your antivirus
2. Run from source instead

---

## 📄 Project Structure

```
IosToJpg/
├── ios_converter_cli.py    # Main converter (CLI version)
├── ios_converter.py        # GUI version (requires Tkinter)
├── build_exe.py            # Script to build standalone exe
├── convert.bat             # Windows batch launcher
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── ffmpeg_bin/
│   └── ffmpeg.exe          # Bundled FFmpeg
├── dist/
│   └── iOSConverter.exe    # Standalone executable
└── tests/
    └── test_converter.py   # Unit tests
```

---

## 📜 License

MIT License - Feel free to use and modify as needed.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Run tests before submitting
4. Submit a pull request

---

## 📞 Support

If you encounter issues:
1. Run `iOSConverter.exe --check` to verify dependencies
2. Check the Troubleshooting section above
3. Open an issue with error details
