#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced microphone transcription script using Parakeet MLX with advanced features.

This script creates a real-time speech-to-text transcription system with advanced features like:
- Word-level timestamps
- Chunking for continuous transcription
- Saving outputs in various formats
- Enhanced visualization of transcription results
"""

import os
import sys
import time
import queue
import signal
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any

import mlx.core as mx
import numpy as np
import sounddevice as sd
from parakeet_mlx import from_pretrained, AlignedResult, AlignedSentence, AlignedToken
from parakeet_mlx.audio import get_logmel

# Configuration
MODEL_NAME = "mlx-community/parakeet-tdt-0.6b-v2"  # Parakeet model
SAMPLE_RATE = 16000  # Sample rate Parakeet expects
BUFFER_DURATION = 5  # Process 5 seconds of audio at a time
CHANNELS = 1  # Mono audio
CHUNK_DURATION = 20.0  # Duration of chunks to process (in seconds)
OVERLAP_DURATION = 4.0  # Overlap between chunks (in seconds)

# Terminal colors for prettier output
COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

# For storing audio data
audio_queue = queue.Queue()
all_transcriptions = []  # Store all transcriptions for saving later
transcription_lock = threading.Lock()

# State tracking
@dataclass
class TranscriptionState:
    latest_text: str = ""
    current_chunk: np.ndarray = None
    chunk_duration: float = 0.0
    chunks_processed: int = 0
    recording_started: Optional[float] = None
    is_speaking: bool = False
    silence_start: Optional[float] = None
    last_update: Optional[float] = None

# Global state
state = TranscriptionState()

# Flag to signal when to stop
stop_event = threading.Event()

# Set device to CPU for stable performance
mx.set_default_device(mx.cpu)

def colored(text, color):
    """Apply color to terminal text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['ENDC']}"

def audio_callback(indata, frames, time_info, status):
    """Callback function for sounddevice to capture audio."""
    if status:
        print(f"{colored('Audio status:', 'YELLOW')} {status}")
    
    # Add the audio data to the queue without blocking
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        print(colored("Audio queue is full, dropping data!", "RED"))

def get_timestamp_display(timestamp):
    """Convert seconds to MM:SS format."""
    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    return f"{minutes:02d}:{seconds:02d}"

def display_result(result: AlignedResult, elapsed_time: float, is_final: bool = False):
    """Display transcription results in a nicely formatted way."""
    # Clear previous lines if updating
    if state.last_update and not is_final:
        print("\033[F\033[K" * 3, end="")
    
    # Display header
    status = colored("FINAL", "GREEN") if is_final else colored("INTERIM", "YELLOW")
    print(f"\n{colored('Transcription:', 'HEADER')} [{status}] {colored(f'(RTF: {elapsed_time:.2f}x)', 'CYAN')}")
    
    # Display text (with a fallback if empty)
    text_to_display = result.text if result.text else "[No speech detected]"
    print(f"{colored(text_to_display, 'BOLD')}")
    
    # Display word-level timestamps (last sentence only for ongoing transcriptions)
    if result.sentences and len(result.sentences) > 0:
        display_sentence = result.sentences[-1]
        if display_sentence and hasattr(display_sentence, 'tokens') and display_sentence.tokens:
            timestamp_display = ""
            for token in display_sentence.tokens:
                if token.text.strip():
                    timestamp_display += f"{colored(token.text, 'BLUE')}[{get_timestamp_display(token.start)}] "
            if timestamp_display:
                print(timestamp_display)
    
    # Update last update time
    state.last_update = time.time()

def save_transcriptions(output_dir="transcriptions", output_formats=["txt", "srt", "json"]):
    """Save transcriptions to specified formats."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Combine all transcriptions into one result
    if not all_transcriptions:
        print(colored("No transcriptions to save.", "YELLOW"))
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = os.path.join(output_dir, f"transcription_{timestamp}")
    
    # Create text file
    if "txt" in output_formats:
        with open(f"{filename_base}.txt", "w") as f:
            for result in all_transcriptions:
                for sentence in result.sentences:
                    f.write(f"[{get_timestamp_display(sentence.start)} - {get_timestamp_display(sentence.end)}] {sentence.text}\n")
        print(colored(f"Saved transcript to {filename_base}.txt", "GREEN"))
    
    # Create SRT file
    if "srt" in output_formats:
        with open(f"{filename_base}.srt", "w") as f:
            index = 1
            for result in all_transcriptions:
                for sentence in result.sentences:
                    # Format time as SRT timestamp (HH:MM:SS,mmm)
                    start_time = f"{int(sentence.start // 3600):02d}:{int((sentence.start % 3600) // 60):02d}:{int(sentence.start % 60):02d},{int((sentence.start % 1) * 1000):03d}"
                    end_time = f"{int(sentence.end // 3600):02d}:{int((sentence.end % 3600) // 60):02d}:{int(sentence.end % 60):02d},{int((sentence.end % 1) * 1000):03d}"
                    
                    f.write(f"{index}\n{start_time} --> {end_time}\n{sentence.text}\n\n")
                    index += 1
        print(colored(f"Saved transcript to {filename_base}.srt", "GREEN"))
    
    # Create JSON file
    if "json" in output_formats:
        import json
        
        # Convert to serializable format
        json_data = []
        for result in all_transcriptions:
            sentences = []
            for sentence in result.sentences:
                tokens = []
                for token in sentence.tokens:
                    tokens.append({
                        "text": token.text,
                        "start": token.start,
                        "end": token.end,
                        "duration": token.duration
                    })
                sentences.append({
                    "text": sentence.text,
                    "start": sentence.start,
                    "end": sentence.end,
                    "duration": sentence.duration,
                    "tokens": tokens
                })
            json_data.append({
                "text": result.text,
                "sentences": sentences
            })
        
        with open(f"{filename_base}.json", "w") as f:
            json.dump(json_data, f, indent=2)
        print(colored(f"Saved transcript to {filename_base}.json", "GREEN"))

def process_audio(device=None, enable_chunking=True):
    """Process audio data and generate transcriptions with enhanced features."""
    global state
    
    # Buffer to accumulate audio
    audio_buffer = np.empty((0, CHANNELS), dtype=np.float32)
    buffer_size = int(BUFFER_DURATION * SAMPLE_RATE)
    
    # Chunk parameters for continuous transcription
    chunk_size = int(CHUNK_DURATION * SAMPLE_RATE) if enable_chunking else None
    overlap_size = int(OVERLAP_DURATION * SAMPLE_RATE) if enable_chunking else None
    
    print(colored("Loading Parakeet model...", "BLUE"))
    start_time = time.time()
    model = from_pretrained(MODEL_NAME, dtype=mx.float32)
    load_time = time.time() - start_time
    print(colored(f"Model loaded in {load_time:.2f} seconds!", "GREEN"))
    
    print("\n" + colored("===== TRANSCRIPTION STARTED =====", "HEADER") + "\n")
    device_info = f" from device: {device}" if device else ""
    print(colored(f"Listening{device_info}... (Press Ctrl+C to stop)", "BLUE") + "\n")
    
    # Record the start time of the recording
    state.recording_started = time.time()
    
    # Keep track of all audio for chunking
    all_audio = np.empty((0, CHANNELS), dtype=np.float32) if enable_chunking else None
    
    while not stop_event.is_set():
        try:
            # Get audio data with timeout to check stop_event regularly
            new_audio = audio_queue.get(timeout=0.5)
            audio_buffer = np.vstack((audio_buffer, new_audio))
            audio_queue.task_done()
            
            # If chunking is enabled, add to all_audio
            if enable_chunking and all_audio is not None:
                all_audio = np.vstack((all_audio, new_audio))
            
            # Once we have enough audio data, process it
            if len(audio_buffer) >= buffer_size:
                # Extract a chunk of audio data
                current_chunk = audio_buffer[:buffer_size].copy()
                audio_buffer = audio_buffer[buffer_size:]
                
                # Process using full chunking algorithm if enabled and we have enough data
                if enable_chunking and all_audio is not None and len(all_audio) >= chunk_size:
                    # Extract the current chunk to process
                    chunk_to_process = all_audio[:chunk_size].copy()
                    
                    # Keep the overlap for the next chunk
                    if overlap_size is not None and overlap_size > 0:
                        all_audio = all_audio[chunk_size-overlap_size:]
                    else:
                        all_audio = all_audio[chunk_size:]
                    
                    # Process the chunk with the model
                    process_start = time.time()
                    
                    # Preprocessing: clip and convert to float32
                    processed_chunk = np.clip(chunk_to_process, -1.0, 1.0).astype(np.float32)
                    
                    # Convert to 1D array (flatten) if mono
                    audio_1d = processed_chunk.flatten()
                    
                    # Convert to MLX array
                    audio_mlx = mx.array(audio_1d)
                    
                    # Extract mel spectrogram features
                    mel = get_logmel(audio_mlx, model.preprocessor_config)
                    
                    # Generate transcription
                    result = model.generate(mel)
                    
                    # Handle different return types
                    if isinstance(result, list) and len(result) > 0:
                        result = result[0]
                    
                    # Ensure we have a valid AlignedResult
                    if not hasattr(result, 'text'):
                        print(colored(f"Warning: Got unexpected result type: {type(result)}", "YELLOW"))
                        continue
                    
                    process_time = time.time() - process_start
                    rtf = process_time / CHUNK_DURATION
                    
                    # Store the result
                    with transcription_lock:
                        all_transcriptions.append(result)
                        state.latest_text = result.text if hasattr(result, 'text') and result.text else state.latest_text
                    
                    # Display and update state
                    display_result(result, rtf, True)
                    state.chunks_processed += 1
                    
                # Process an individual segment (used when chunking is disabled or during startup)
                else:
                    # Preprocessing: clip and convert to float32
                    processed_chunk = np.clip(current_chunk, -1.0, 1.0).astype(np.float32)
                    
                    # Convert to 1D array (flatten) if mono
                    audio_1d = processed_chunk.flatten()
                    
                    # Process timing
                    process_start = time.time()
                    
                    # Convert to MLX array
                    audio_mlx = mx.array(audio_1d)
                    
                    # Extract mel spectrogram features
                    mel = get_logmel(audio_mlx, model.preprocessor_config)
                    
                    # Generate transcription
                    result = model.generate(mel)
                    
                    # Handle different return types
                    if isinstance(result, list) and len(result) > 0:
                        result = result[0]
                    
                    # Ensure we have a valid AlignedResult
                    if not hasattr(result, 'text'):
                        print(colored(f"Warning: Got unexpected result type in interim processing: {type(result)}", "YELLOW"))
                        continue
                    
                    process_time = time.time() - process_start
                    rtf = process_time / BUFFER_DURATION
                    
                    # Update state and display
                    with transcription_lock:
                        state.latest_text = result.text if hasattr(result, 'text') and result.text else state.latest_text
                    
                    # Display interim results
                    display_result(result, rtf, False)  
        
        except queue.Empty:
            # No new audio data within timeout period
            continue
        except Exception as e:
            print(colored(f"Error in audio processing: {e}", "RED"))
            import traceback
            traceback.print_exc()
    
    print("\n" + colored("Transcription complete.", "GREEN"))
    return all_transcriptions

def main():
    """Main function to run the enhanced transcription."""
    # Declare globals at the beginning of the function
    global MODEL_NAME, CHUNK_DURATION, OVERLAP_DURATION
    
    import sys
    import signal
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Enhanced real-time speech transcription with Parakeet MLX")
    parser.add_argument(
        "--device", type=str, default=None, 
        help="Audio input device (leave blank to use default)"
    )
    parser.add_argument(
        "--list-devices", action="store_true",
        help="List available audio input devices and exit"
    )
    parser.add_argument(
        "--model", type=str, default=MODEL_NAME,
        help=f"Parakeet model to use (default: {MODEL_NAME})"
    )
    parser.add_argument(
        "--no-chunking", action="store_true",
        help="Disable chunking for continuous transcription"
    )
    parser.add_argument(
        "--chunk-duration", type=float, default=CHUNK_DURATION,
        help=f"Duration of each chunk in seconds (default: {CHUNK_DURATION})"
    )
    parser.add_argument(
        "--overlap-duration", type=float, default=OVERLAP_DURATION,
        help=f"Overlap between chunks in seconds (default: {OVERLAP_DURATION})"
    )
    parser.add_argument(
        "--output-dir", type=str, default="transcriptions",
        help="Directory to save transcriptions (default: transcriptions)"
    )
    parser.add_argument(
        "--output-format", type=str, default="all",
        help="Output format (txt/srt/json/all)"
    )
    
    args = parser.parse_args()
    
    # Update global variables with command-line arguments
    MODEL_NAME = args.model
    CHUNK_DURATION = args.chunk_duration
    OVERLAP_DURATION = args.overlap_duration
    
    # List audio devices if requested
    if args.list_devices:
        print(colored("Available audio devices:", "HEADER"))
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:  # Only show input devices
                print(f"{colored(str(i), 'GREEN')}: {device['name']} (Inputs: {device['max_input_channels']})")
        return
    
    # Define signal handler for CTRL+C
    def signal_handler(sig, frame):
        print("\n" + colored("CTRL+C detected. Stopping transcription...", "YELLOW"))
        stop_event.set()
    
    # Register our signal handler for CTRL+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start processing thread
    process_thread = threading.Thread(
        target=process_audio, 
        args=(args.device, not args.no_chunking)
    )
    process_thread.daemon = True  # Thread will exit when main thread exits
    process_thread.start()
    
    # Variable to hold the audio stream
    stream = None
    
    try:
        # Start audio input stream
        stream = sd.InputStream(
            device=args.device,
            samplerate=SAMPLE_RATE, 
            channels=CHANNELS,
            callback=audio_callback,
            dtype='float32'
        )
        stream.start()
        
        # Keep running until program is terminated
        while not stop_event.is_set():
            time.sleep(0.1)
            
    except Exception as e:
        print(colored(f"Error with audio stream: {e}", "RED"))
        if stream is None:
            print(colored("Failed to open audio stream. Try listing available devices:", "YELLOW"))
            print(colored("  python enhanced_transcription.py --list-devices", "CYAN"))
        stop_event.set()
    
    finally:
        # This should run during normal shutdown
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception as e:
                print(colored(f"Error stopping audio stream: {e}", "RED"))
        
        # Wait for processing thread to finish
        if process_thread.is_alive():
            process_thread.join(timeout=2.0)
        
        # Save transcriptions if we have any
        with transcription_lock:
            if all_transcriptions:
                output_formats = args.output_format.lower().split(",")
                if "all" in output_formats:
                    output_formats = ["txt", "srt", "json"]
                save_transcriptions(args.output_dir, output_formats)
        
        print(colored("\n===== TRANSCRIPTION ENDED =====\n", "HEADER"))
        print(colored("Thank you for using Enhanced Parakeet Transcription!", "GREEN"))

if __name__ == "__main__":
    main()