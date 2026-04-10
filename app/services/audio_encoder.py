"""Encode raw PCM samples to various audio formats using ffmpeg."""

import io
import subprocess
import numpy as np
import static_ffmpeg

# Ensure static ffmpeg binary is on PATH
static_ffmpeg.add_paths()

SUPPORTED_FORMATS = {"mp3", "wav", "opus", "flac", "aac", "pcm"}

FORMAT_CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/opus",
    "flac": "audio/flac",
    "aac": "audio/aac",
    "pcm": "audio/pcm",
}

# ffmpeg output format flags
_FFMPEG_FORMAT = {
    "mp3": ["-f", "mp3", "-codec:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-f", "wav"],
    "opus": ["-f", "opus", "-codec:a", "libopus"],
    "flac": ["-f", "flac"],
    "aac": ["-f", "adts", "-codec:a", "aac"],
}


def encode_audio(
    samples: np.ndarray,
    sample_rate: int,
    output_format: str = "mp3",
) -> bytes:
    """Convert float32 PCM samples to the requested audio format.

    Args:
        samples: numpy float32 array of audio samples
        sample_rate: sample rate (e.g. 24000)
        output_format: one of mp3, wav, opus, flac, aac, pcm

    Returns:
        Encoded audio bytes
    """
    if output_format == "pcm":
        # Raw 16-bit signed LE mono
        pcm_16 = (samples * 32767).astype(np.int16)
        return pcm_16.tobytes()

    if output_format not in _FFMPEG_FORMAT:
        raise ValueError(f"Unsupported format: {output_format}")

    # Convert float32 -> 16-bit PCM bytes for ffmpeg stdin
    pcm_16 = (samples * 32767).astype(np.int16)
    pcm_bytes = pcm_16.tobytes()

    cmd = [
        "ffmpeg",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        "-i", "pipe:0",
        *_FFMPEG_FORMAT[output_format],
        "-y",
        "pipe:1",
    ]

    proc = subprocess.run(
        cmd,
        input=pcm_bytes,
        capture_output=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg encoding failed: {proc.stderr.decode()}")

    return proc.stdout


def encode_audio_stream(
    samples: np.ndarray,
    sample_rate: int,
    output_format: str = "mp3",
) -> subprocess.Popen:
    """Start an ffmpeg process for streaming encoding.

    Write PCM chunks to proc.stdin, read encoded audio from proc.stdout.

    Args:
        samples: not used directly — caller writes to proc.stdin
        sample_rate: sample rate
        output_format: target format

    Returns:
        subprocess.Popen with stdin/stdout pipes
    """
    if output_format == "pcm":
        return None  # no encoding needed for raw PCM

    if output_format not in _FFMPEG_FORMAT:
        raise ValueError(f"Unsupported format: {output_format}")

    cmd = [
        "ffmpeg",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        "-i", "pipe:0",
        *_FFMPEG_FORMAT[output_format],
        "-y",
        "pipe:1",
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
