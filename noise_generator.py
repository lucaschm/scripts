#!/usr/bin/env python3
import argparse
import numpy as np
from scipy.io import wavfile


def generate_tone_signal(frequency: float, duration: float, sample_rate: int) -> np.ndarray:
    """Generate a sine tone signal."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)


def generate_white_noise(n_samples: int) -> np.ndarray:
    """Generate white noise (Gaussian)."""
    return np.random.randn(n_samples)


def generate_brown_noise(n_samples: int) -> np.ndarray:
    """Generate brown noise (integrated white noise / random walk)."""
    white = np.random.randn(n_samples)
    brown = np.cumsum(white)                # random walk
    brown -= brown.mean()                   # remove DC offset
    brown /= np.max(np.abs(brown))          # normalize to [-1, 1]
    return brown


def generate_pink_noise(n_samples: int, sample_rate: int) -> np.ndarray:
    """Generate pink noise using 1/f frequency-domain shaping."""
    white = np.random.randn(n_samples)
    white_fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n_samples, d=1 / sample_rate)

    # 1/sqrt(f) scaling, ignore DC
    scale = np.ones_like(freqs)
    scale[1:] = 1 / np.sqrt(freqs[1:])
    pink_fft = white_fft * scale

    pink = np.fft.irfft(pink_fft, n_samples)
    pink -= pink.mean()
    pink /= np.max(np.abs(pink))            # normalize to [-1, 1]
    return pink


def write_wav_from_signal(filename: str, signal: np.ndarray,
                          sample_rate: int = 44100, volume: float = 0.5) -> None:
    """Scale a signal to 16‑bit PCM and write it as a mono WAV file."""
    # Ensure finite values
    signal = np.nan_to_num(signal)

    # Apply volume and clip to [-1, 1]
    signal = np.clip(signal * volume, -1.0, 1.0)

    # Convert to 16‑bit PCM
    signal_int16 = (signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, signal_int16)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate tone or colored noise WAV for sleep."
    )
    parser.add_argument(
        "frequency",
        type=float,
        help="Tone frequency in Hz (used only in tone mode)."
    )
    parser.add_argument(
        "duration",
        type=float,
        help="Duration in seconds."
    )
    parser.add_argument(
        "output",
        type=str,
        help="Output WAV filename (e.g. sleep.wav)."
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["tone", "white", "pink", "brown"],
        default="tone",
        help="What to generate: tone, white, pink, or brown (default: tone)."
    )
    parser.add_argument(
        "--sample-rate",
        "-r",
        type=int,
        default=44100,
        help="Sample rate in Hz (default: 44100)."
    )
    parser.add_argument(
        "--volume",
        "-v",
        type=float,
        default=0.5,
        help="Volume from 0.0 to 1.0 (default: 0.5)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    n_samples = int(args.sample_rate * args.duration)

    if args.mode == "tone":
        signal = generate_tone_signal(args.frequency, args.duration, args.sample_rate)
    elif args.mode == "white":
        signal = generate_white_noise(n_samples)
    elif args.mode == "pink":
        signal = generate_pink_noise(n_samples, args.sample_rate)
    elif args.mode == "brown":
        signal = generate_brown_noise(n_samples)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

    write_wav_from_signal(
        filename=args.output,
        signal=signal,
        sample_rate=args.sample_rate,
        volume=args.volume,
    )


if __name__ == "__main__":
    main()
