# Enhanced Parakeet Transcription

A real-time speech transcription system using Parakeet MLX for Apple Silicon. This tool captures audio from your microphone and provides real-time transcription with word-level timestamps, continuous chunking, and multi-format export capabilities.

![Parakeet MLX](https://img.shields.io/badge/Parakeet-MLX-orange)
![Apple Silicon](https://img.shields.io/badge/Apple-Silicon-blue)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green)

## Features

- **Real-time transcription** of microphone input
- **Word-level timestamps** to know exactly when each word was spoken
- **Continuous chunking** for longer recordings with overlapping context
- **Multi-format export** (TXT, SRT subtitles, and JSON)
- **Colorized output** for better visualization
- **Device selection** for systems with multiple microphones

## Installation

### Prerequisites

- Python 3.9 or higher
- macOS with Apple Silicon (M1, M2, M3, etc.)
- A working microphone

### Installation with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast package installer for Python. To install the required dependencies using UV:

```bash
# Install uv if you haven't already
curl -fsSL https://astral.sh/uv/install.sh | bash

# Create and activate a new environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install mlx parakeet-mlx sounddevice numpy
```

### Installation with pip

If you prefer using pip instead:

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install mlx parakeet-mlx sounddevice numpy
```

## Usage

### Basic Usage

To start transcription with default settings:

```bash
python enhanced_transcription.py
```

### List Available Audio Devices

To see all available audio input devices on your system:

```bash
python enhanced_transcription.py --list-devices
```

### Select a Specific Audio Device

To use a specific audio input device:

```bash
python enhanced_transcription.py --device "Device Name"
# Or use the device number
python enhanced_transcription.py --device 1
```

### Customizing Chunking

To adjust how audio is processed in chunks:

```bash
# Disable chunking (process in small segments only)
python enhanced_transcription.py --no-chunking

# Customize chunk duration and overlap
python enhanced_transcription.py --chunk-duration 15 --overlap-duration 3
```

### Specifying Output Formats

Choose which output formats to save:

```bash
# Save only as SRT subtitle file
python enhanced_transcription.py --output-format srt

# Save in multiple formats
python enhanced_transcription.py --output-format txt,json

# Save in all formats (default)
python enhanced_transcription.py --output-format all
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|--------|
| `--device` | Audio input device name or index | System default |
| `--list-devices` | List all available audio devices and exit | - |
| `--model` | Parakeet model to use | mlx-community/parakeet-tdt-0.6b-v2 |
| `--no-chunking` | Disable chunking for continuous transcription | False |
| `--chunk-duration` | Duration of each chunk in seconds | 20.0 |
| `--overlap-duration` | Overlap between chunks in seconds | 4.0 |
| `--output-dir` | Directory to save transcriptions | transcriptions |
| `--output-format` | Output format (txt/srt/json/all) | all |

## How It Works

The enhanced transcription system works through several coordinated components:

### 1. Audio Capture

The script captures audio from your selected microphone using the `sounddevice` library. Audio is captured in a non-blocking way and stored in a thread-safe queue for processing.

### 2. Processing Pipeline

The captured audio goes through a processing pipeline:

1. **Preprocessing**: Audio is normalized and converted to the format expected by the model
2. **Feature Extraction**: Audio is converted to log-mel spectrograms using Parakeet's preprocessing
3. **Transcription**: The Parakeet model generates transcription with timestamps
4. **Post-processing**: Results are formatted and displayed/saved

### 3. Chunking Strategy

For longer recordings, the script uses a chunking strategy:

- Audio is processed in overlapping chunks (default: 20 seconds with 4 second overlap)
- This allows for continuous transcription while maintaining context between chunks
- The overlap helps prevent words from being cut off at chunk boundaries

### 4. Visualization and Export

The script provides:

- Real-time visualization of transcriptions with word-level timestamps
- Progress indicators showing Real-Time Factor (RTF) - how fast processing is compared to audio duration
- Export capabilities in multiple formats

## Components Overview

### TranscriptionState Class

Tracks the current state of the transcription process, including:

- Latest transcribed text
- Current audio chunk being processed
- Statistics about chunks processed
- Recording start time and duration

### Audio Processing Functions

- `audio_callback`: Captures audio from the microphone
- `process_audio`: Main function that processes audio chunks and generates transcriptions
- `get_logmel`: Converts audio to log-mel spectrograms for the model

### Visualization and Display

- `colored`: Applies terminal colors for better visualization
- `display_result`: Formats and displays transcription results
- `get_timestamp_display`: Formats timestamps in human-readable format

### Export Functions

- `save_transcriptions`: Saves transcriptions in various formats

## Troubleshooting

### No Audio Detected

If the script doesn't detect any audio:

1. Check your microphone is working and properly connected
2. Use `--list-devices` to verify your audio device is detected
3. Try selecting a specific device with `--device`

### Poor Transcription Quality

If transcription quality is poor:

1. Ensure you're in a quiet environment
2. Speak clearly and at a normal pace
3. Try adjusting chunk size parameters for your speaking style

### Script Crashes or Hangs

If the script crashes or hangs:

1. Make sure you have sufficient memory available
2. Try running with shorter chunk durations (`--chunk-duration 10`)
3. Update to the latest versions of dependencies

## Advanced Usage

### Integration with Other Tools

The `enhanced_transcription.py` script can be integrated with other tools:

- **Video subtitling**: Use the SRT output with video editing software
- **Speech analysis**: Use the JSON output for analyzing speech patterns
- **Automated documentation**: Pipe the TXT output to a documentation generator

### Overlaying GIFs onto a Video

The repository includes a small utility (`overlay_gif.py`) that demonstrates how
to place an animated GIF on top of an MP4 file. The script can trim the input
video to a specific range and control when the GIF appears and disappears. It
relies on the [`moviepy`](https://zulko.github.io/moviepy/) library.

If you haven't installed `moviepy`, you can do so with:

```bash
pip install moviepy
```

Basic usage:

```bash
python overlay_gif.py --video input.mp4 --gif anim.gif \
    --gif-start 5 --position center --output output.mp4
```

This inserts `anim.gif` in the center of `input.mp4`, starting five seconds into
the video, and saves the result as `output.mp4`.

You can also trim the source video and specify when the GIF disappears:

```bash
python overlay_gif.py --video input.mp4 --gif anim.gif \
    --clip-start 10 --clip-end 20 \
    --gif-start 2 --gif-end 8 --position "100,200" \
    --output clipped.mp4
```

This cuts `input.mp4` to the 10–20 second range and overlays `anim.gif` at the
coordinates (100, 200) from two seconds into the clip until the eight-second
mark.

### Customizing the Model

You can use different Parakeet models with the `--model` parameter:

```bash
# Use a different model from Hugging Face
python enhanced_transcription.py --model "mlx-community/parakeet-rnnt-1.1b"
```

## License

This project is available under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- [Parakeet MLX](https://github.com/senstella/parakeet-mlx) for the excellent speech recognition model
- [MLX](https://github.com/ml-explore/mlx) for the machine learning framework optimized for Apple Silicon
- [Sounddevice](https://github.com/spatialaudio/python-sounddevice) for audio capture functionality