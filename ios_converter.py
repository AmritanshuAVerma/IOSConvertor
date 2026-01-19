"""
iOS Format Converter
Converts iOS formats (HEIC/HEIF images, MOV videos) to PNG and MP4
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
from tkinter import Tk, Frame, Label, Button, filedialog, messagebox, StringVar, OptionMenu, ttk
from tkinter.scrolledtext import ScrolledText

# Try to import pillow-heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class IOSConverter:
    """Main converter class for iOS formats"""
    
    SUPPORTED_IMAGE_FORMATS = ['.heic', '.heif']
    SUPPORTED_VIDEO_FORMATS = ['.mov', '.m4v']
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self):
        """Find ffmpeg executable"""
        # Check if ffmpeg is in PATH
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                    capture_output=True, text=True)
            if result.returncode == 0:
                return 'ffmpeg'
        except FileNotFoundError:
            pass
        
        # Common installation paths on Windows
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def convert_heic_to_png(self, input_path, output_path=None, callback=None):
        """Convert HEIC/HEIF image to PNG"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow is not installed. Run: pip install Pillow")
        
        if not HEIF_SUPPORT:
            raise RuntimeError("pillow-heif is not installed. Run: pip install pillow-heif")
        
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.with_suffix('.png')
        else:
            output_path = Path(output_path)
        
        if callback:
            callback(f"Converting: {input_path.name} -> {output_path.name}")
        
        # Open and convert the image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (HEIC might have alpha)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # Keep transparency for PNG
                img.save(output_path, 'PNG')
            else:
                img.convert('RGB').save(output_path, 'PNG')
        
        if callback:
            callback(f"✓ Completed: {output_path.name}")
        
        return output_path
    
    def convert_mov_to_mp4(self, input_path, output_path=None, callback=None):
        """Convert MOV video to MP4"""
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg is not installed or not found in PATH.\n"
                             "Please install FFmpeg from https://ffmpeg.org/download.html")
        
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.with_suffix('.mp4')
        else:
            output_path = Path(output_path)
        
        if callback:
            callback(f"Converting: {input_path.name} -> {output_path.name}")
        
        # FFmpeg command for MOV to MP4 conversion
        # Using H.264 codec for wide compatibility
        cmd = [
            self.ffmpeg_path,
            '-i', str(input_path),
            '-c:v', 'libx264',      # Video codec
            '-preset', 'medium',     # Encoding speed/quality balance
            '-crf', '23',            # Quality (lower = better, 18-28 is good range)
            '-c:a', 'aac',           # Audio codec
            '-b:a', '128k',          # Audio bitrate
            '-movflags', '+faststart',  # Enable streaming
            '-y',                    # Overwrite output
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
        except Exception as e:
            raise RuntimeError(f"Conversion failed: {str(e)}")
        
        if callback:
            callback(f"✓ Completed: {output_path.name}")
        
        return output_path
    
    def convert_file(self, input_path, output_dir=None, callback=None):
        """Convert a single file based on its extension"""
        input_path = Path(input_path)
        ext = input_path.suffix.lower()
        
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = input_path.parent
        
        if ext in self.SUPPORTED_IMAGE_FORMATS:
            output_path = output_dir / (input_path.stem + '.png')
            return self.convert_heic_to_png(input_path, output_path, callback)
        elif ext in self.SUPPORTED_VIDEO_FORMATS:
            output_path = output_dir / (input_path.stem + '.mp4')
            return self.convert_mov_to_mp4(input_path, output_path, callback)
        else:
            raise ValueError(f"Unsupported format: {ext}")
    
    def batch_convert(self, input_paths, output_dir=None, callback=None):
        """Convert multiple files"""
        results = []
        for path in input_paths:
            try:
                result = self.convert_file(path, output_dir, callback)
                results.append(('success', path, result))
            except Exception as e:
                if callback:
                    callback(f"✗ Failed: {Path(path).name} - {str(e)}")
                results.append(('error', path, str(e)))
        return results


class ConverterGUI:
    """GUI for iOS Format Converter"""
    
    def __init__(self):
        self.converter = IOSConverter()
        self.files_to_convert = []
        
        self.root = Tk()
        self.root.title("iOS Format Converter")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        self._setup_ui()
        self._check_dependencies()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = Label(main_frame, text="iOS Format Converter", 
                           font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = Label(main_frame, 
                              text="Convert HEIC/HEIF → PNG  |  MOV/M4V → MP4",
                              font=('Arial', 10), fg='gray')
        subtitle_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = Frame(main_frame)
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.status_var = StringVar(value="Ready")
        status_label = Label(status_frame, textvariable=self.status_var,
                            font=('Arial', 10), fg='blue')
        status_label.pack()
        
        # Buttons frame
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill='x', pady=10)
        
        # Select Files button
        select_btn = Button(btn_frame, text="📁 Select Files", 
                           command=self._select_files,
                           font=('Arial', 11), width=15, height=2)
        select_btn.pack(side='left', padx=5)
        
        # Select Folder button
        folder_btn = Button(btn_frame, text="📂 Select Folder", 
                           command=self._select_folder,
                           font=('Arial', 11), width=15, height=2)
        folder_btn.pack(side='left', padx=5)
        
        # Clear button
        clear_btn = Button(btn_frame, text="🗑️ Clear", 
                          command=self._clear_files,
                          font=('Arial', 11), width=10, height=2)
        clear_btn.pack(side='left', padx=5)
        
        # Output directory frame
        output_frame = Frame(main_frame)
        output_frame.pack(fill='x', pady=15)
        
        Label(output_frame, text="Output Directory:", 
              font=('Arial', 10)).pack(side='left')
        
        self.output_var = StringVar(value="Same as source")
        self.output_label = Label(output_frame, textvariable=self.output_var,
                                  font=('Arial', 10), fg='gray')
        self.output_label.pack(side='left', padx=10)
        
        output_btn = Button(output_frame, text="Change...", 
                           command=self._select_output_dir)
        output_btn.pack(side='right')
        
        self.output_dir = None
        
        # File list
        list_frame = Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        Label(list_frame, text="Files to Convert:", 
              font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.file_list = ScrolledText(list_frame, height=8, width=70,
                                       font=('Consolas', 9))
        self.file_list.pack(fill='both', expand=True, pady=5)
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill='x', pady=10)
        
        # Log area
        log_frame = Frame(main_frame)
        log_frame.pack(fill='both', expand=True, pady=5)
        
        Label(log_frame, text="Conversion Log:", 
              font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.log_area = ScrolledText(log_frame, height=6, width=70,
                                      font=('Consolas', 9))
        self.log_area.pack(fill='both', expand=True, pady=5)
        
        # Convert button
        self.convert_btn = Button(main_frame, text="🔄 Convert All", 
                                  command=self._start_conversion,
                                  font=('Arial', 12, 'bold'), 
                                  width=20, height=2,
                                  bg='#4CAF50', fg='white')
        self.convert_btn.pack(pady=15)
    
    def _check_dependencies(self):
        """Check and report missing dependencies"""
        warnings = []
        
        if not PIL_AVAILABLE:
            warnings.append("⚠️ Pillow not installed (pip install Pillow)")
        
        if not HEIF_SUPPORT:
            warnings.append("⚠️ pillow-heif not installed (pip install pillow-heif)")
        
        if not self.converter.ffmpeg_path:
            warnings.append("⚠️ FFmpeg not found (needed for video conversion)")
        
        if warnings:
            self._log("\n".join(warnings))
            self._log("Some features may be unavailable.\n")
        else:
            self._log("✓ All dependencies are available.\n")
    
    def _log(self, message):
        """Add message to log area"""
        self.log_area.insert('end', message + '\n')
        self.log_area.see('end')
        self.root.update_idletasks()
    
    def _update_file_list(self):
        """Update the file list display"""
        self.file_list.delete('1.0', 'end')
        for f in self.files_to_convert:
            self.file_list.insert('end', f + '\n')
        self.status_var.set(f"{len(self.files_to_convert)} file(s) selected")
    
    def _select_files(self):
        """Open file dialog to select files"""
        filetypes = [
            ("iOS Formats", "*.heic *.heif *.mov *.m4v"),
            ("HEIC/HEIF Images", "*.heic *.heif"),
            ("MOV Videos", "*.mov *.m4v"),
            ("All Files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select iOS Format Files",
            filetypes=filetypes
        )
        
        if files:
            self.files_to_convert.extend(files)
            self._update_file_list()
    
    def _select_folder(self):
        """Select a folder and add all supported files"""
        folder = filedialog.askdirectory(title="Select Folder with iOS Files")
        
        if folder:
            supported_exts = (self.converter.SUPPORTED_IMAGE_FORMATS + 
                           self.converter.SUPPORTED_VIDEO_FORMATS)
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in supported_exts:
                        self.files_to_convert.append(os.path.join(root, file))
            
            self._update_file_list()
    
    def _select_output_dir(self):
        """Select output directory"""
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_dir = folder
            self.output_var.set(folder)
    
    def _clear_files(self):
        """Clear the file list"""
        self.files_to_convert = []
        self._update_file_list()
        self.status_var.set("Ready")
    
    def _start_conversion(self):
        """Start the conversion process in a separate thread"""
        if not self.files_to_convert:
            messagebox.showwarning("No Files", "Please select files to convert.")
            return
        
        self.convert_btn.config(state='disabled')
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.files_to_convert)
        
        # Run conversion in separate thread
        thread = threading.Thread(target=self._convert_files)
        thread.daemon = True
        thread.start()
    
    def _convert_files(self):
        """Convert all files (runs in separate thread)"""
        total = len(self.files_to_convert)
        success = 0
        failed = 0
        
        for i, file_path in enumerate(self.files_to_convert):
            try:
                self.converter.convert_file(
                    file_path, 
                    self.output_dir,
                    callback=lambda msg: self.root.after(0, self._log, msg)
                )
                success += 1
            except Exception as e:
                self.root.after(0, self._log, f"✗ Error: {Path(file_path).name} - {str(e)}")
                failed += 1
            
            # Update progress
            self.root.after(0, self._update_progress, i + 1)
        
        # Conversion complete
        self.root.after(0, self._conversion_complete, success, failed)
    
    def _update_progress(self, value):
        """Update progress bar"""
        self.progress['value'] = value
    
    def _conversion_complete(self, success, failed):
        """Called when conversion is complete"""
        self.convert_btn.config(state='normal')
        self._log(f"\n{'='*40}")
        self._log(f"Conversion Complete: {success} succeeded, {failed} failed")
        
        if failed == 0:
            messagebox.showinfo("Success", f"Successfully converted {success} file(s)!")
        else:
            messagebox.showwarning("Complete", 
                                  f"Converted {success} file(s).\n{failed} file(s) failed.")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Command line mode
        converter = IOSConverter()
        
        for file_path in sys.argv[1:]:
            if os.path.exists(file_path):
                try:
                    result = converter.convert_file(
                        file_path,
                        callback=lambda msg: print(msg)
                    )
                    print(f"Output: {result}")
                except Exception as e:
                    print(f"Error converting {file_path}: {e}")
            else:
                print(f"File not found: {file_path}")
    else:
        # GUI mode
        app = ConverterGUI()
        app.run()


if __name__ == "__main__":
    main()
