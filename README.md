# 🎬 Gif-Maker V1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

A professional Python GUI application for creating high-quality animated GIFs with advanced region selection, customizable quality settings, and real-time preview capabilities.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Windows
install.bat

# Or manually
pip install -r requirements.txt
```

### 2. Launch Application
```bash
# Windows
launch.bat

# Or manually
python gif_maker.py
```

## ✨ Key Features

### 🎯 Advanced Region Selection
- **Visual Selection**: Click and drag with real-time rectangle feedback
- **Crosshair Cursor**: Professional selection interface
- **Coordinate Display**: Live coordinates and selection preview
- **Multiple Methods**: Manual coordinates, full screen, or browser presets

### 🎬 Professional Recording
- **Customizable Settings**: Adjustable screenshot count (1-100) and timing (0.1-10s)
- **Quality Control**: High/Medium/Low/MAX quality settings with optimized color reproduction
- **Clean Recording**: Window auto-hides during recording for professional output
- **Progress Tracking**: Real-time progress bar and status updates

### 🎞️ Advanced GIF Creation
- **Multiple Quality Levels**: 
  - **Low**: Fast processing, smaller files
  - **Medium**: Balanced quality and size
  - **High**: Enhanced color reproduction
  - **MAX (99%)**: Professional quality with advanced optimization
  - **MAX (100%)**: Maximum quality with perfect color fidelity
- **Smooth Animation**: Customizable playback speed (3-10 FPS)
- **Color Optimization**: Advanced dithering and palette optimization
- **Gradient Handling**: Special algorithms for smooth gradients without banding

### 📊 Real-time Preview
- **In-App Preview**: View generated images without external applications
- **Navigation Controls**: Browse through captured frames
- **Image Information**: Frame count, dimensions, and file size
- **Delete & Refresh**: Manage captured frames directly in the app

## 🎮 How to Use

### 1. Region Selection
- Click **"Select Browser Window Region"**
- Drag to select the area you want to capture
- Use the crosshair cursor for precise selection
- Confirm your selection when satisfied

### 2. Configure Settings
- **Screenshot Count**: Number of frames (1-100 recommended)
- **Interval**: Time between screenshots (0.1-10.0 seconds)
- **Quality**: Choose from Low/Medium/High/MAX settings
- **Playback Speed**: Adjust final GIF animation speed
- **Output File**: Name and location for the generated GIF

### 3. Record & Create
- Click **"Start Recording"** to begin capturing
- The window will hide automatically during recording
- Click **"Create GIF"** to generate the animated GIF
- Use the preview panel to review your results

## ⚙️ Quality Settings Explained

### Low Quality
- **Speed**: ⚡⚡⚡ Very Fast
- **File Size**: 📦 Small
- **Use Case**: Quick demos, web sharing
- **Features**: Basic color optimization

### Medium Quality
- **Speed**: ⚡⚡ Fast
- **File Size**: 📦📦 Medium
- **Use Case**: General purpose, social media
- **Features**: Balanced optimization

### High Quality
- **Speed**: ⚡ Moderate
- **File Size**: 📦📦📦 Large
- **Use Case**: Professional presentations
- **Features**: Enhanced color reproduction, dithering

### MAX (99%) Quality
- **Speed**: ⏳ Slower
- **File Size**: 📦📦📦📦 Large
- **Use Case**: Professional demos, high-quality sharing
- **Features**: Advanced algorithms, adaptive palette, pre-quantization

### MAX (100%) Quality
- **Speed**: ⏳⏳ Slowest
- **File Size**: 📦📦📦📦📦 Largest
- **Use Case**: Maximum quality requirements
- **Features**: Perfect color fidelity, advanced sharpening, refined optimization

## 🛠️ Technical Requirements

- **Python 3.7+**
- **pyautogui**: For screenshot capture and mouse control
- **Pillow (PIL)**: For advanced image processing and GIF creation
- **tkinter**: For GUI interface (included with Python)

## 📁 Project Structure

```
gifmaker_python/
├── gif_maker.py          # Main application (Gif-Maker V1.0)
├── requirements.txt      # Python dependencies
├── install.bat          # Dependency installer
├── launch.bat           # Application launcher
├── ai_suggestions.md    # Future enhancement ideas
└── README.md            # This documentation
```

## 🎯 Best Practices

### For Best Results
1. **Precise Selection**: Only capture the content area, not browser chrome
2. **Stable Setup**: Keep the target window in the same position
3. **Optimal Timing**: Use 0.3-1.0 second intervals for smooth animation
4. **Frame Count**: 8-15 frames work well for most demos
5. **Quality Choice**: Use MAX for professional demos, High for general use

### Performance Tips
- **MAX Quality**: Use for final presentations only (slower processing)
- **Background Processing**: GIF creation runs in background threads
- **Memory Management**: Large frame counts may require more RAM
- **File Size**: Higher quality = larger files, plan accordingly

## 🐛 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python from https://python.org
- Ensure Python is added to your system PATH
- Restart command prompt after installation

**"Package installation failed"**
- Check internet connection
- Try running `pip install pyautogui pillow` manually
- Update pip: `python -m pip install --upgrade pip`

**"Region selection not working"**
- Ensure target window is visible and not minimized
- Try selecting a smaller region first
- Check if other applications are blocking the selection

**"GIF creation fails"**
- Try a lower quality setting first
- Ensure sufficient disk space
- Check if output directory is writable

**"Poor color quality"**
- Use MAX quality settings for best color reproduction
- Ensure source content has good contrast
- Try different quality levels to find the best balance

## 🎉 What's New in V1.0

### Major Features
- ✅ **Professional GUI**: Modern, intuitive interface design
- ✅ **Visual Region Selection**: Click-and-drag with real-time feedback
- ✅ **Advanced Quality Control**: Multiple quality levels with optimization
- ✅ **Real-time Preview**: In-app image viewing and management
- ✅ **Background Processing**: Non-blocking GIF creation
- ✅ **Customizable Playback**: Adjustable animation speed
- ✅ **Clean Recording**: Auto-hide window during capture

### Technical Improvements
- ✅ **Color Optimization**: Advanced dithering and palette algorithms
- ✅ **Gradient Handling**: Special processing for smooth gradients
- ✅ **Error Handling**: Robust error recovery and user feedback
- ✅ **Performance**: Multi-threaded processing for responsiveness
- ✅ **Memory Management**: Efficient handling of large image sets

## 🚀 Future Enhancements

See `ai_suggestions.md` for planned features including:
- Batch processing capabilities
- Advanced editing tools
- Export format options
- Cloud integration
- And much more!

## 📁 Project Structure

```
gifmaker_python/
├── gif_maker.py          # Main application (Gif-Maker V1.0)
├── requirements.txt      # Python dependencies
├── install.bat          # Windows dependency installer
├── launch.bat           # Windows application launcher
├── README.md            # This documentation
├── CHANGELOG.md         # Version history
├── ai_suggestions.md    # Future enhancement ideas
├── LICENSE              # MIT License
└── .gitignore          # Git ignore rules
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and tkinter
- Uses pyautogui for screenshot capture
- Powered by Pillow (PIL) for image processing
- Inspired by the need for easy GIF creation

---

<div align="center">
  <p><strong>Gif-Maker V1.0 - Professional Animated GIF Creation</strong></p>
  <p>Made with ❤️ for content creators and developers</p>
  <p><a href="https://github.com/AfyKirby1/GifMaker">⭐ Star this repository</a></p>
</div>