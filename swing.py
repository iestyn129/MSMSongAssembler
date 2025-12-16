from librosa.effects import time_stretch
from pydub import AudioSegment
import numpy as np


def stretch(segment: AudioSegment, rate: float) -> AudioSegment:
	sample_width: int = segment.sample_width
	max_val: float = float(1 << (8 * sample_width - 1))
	samples: np.ndarray = np.array(segment.get_array_of_samples(), dtype=np.float32)
	samples /= max_val

	if segment.channels == 2:
		left: np.ndarray = samples[::2]
		right: np.ndarray = samples[1::2]

		left_stretch: np.ndarray = time_stretch(left, rate=rate)
		right_stretch: np.ndarray = time_stretch(right, rate=rate)

		y_stretch: np.ndarray = np.empty((left_stretch.size + right_stretch.size,), dtype=np.float32)
		y_stretch[0::2] = left_stretch
		y_stretch[1::2] = right_stretch
	else:
		y_stretch: np.ndarray = time_stretch(samples, rate=rate)

	y_stretch = np.clip(y_stretch, -1.0, 1.0)
	y_stretch = (y_stretch * max_val).astype(np.int16 if sample_width == 2 else np.int32)

	return segment._spawn(y_stretch.tobytes(), overrides={
		"frame_rate": segment.frame_rate,
		"channels": segment.channels,
		"sample_width": segment.sample_width,
	})


def swing(song: AudioSegment, bpm: int) -> AudioSegment:
	subdivision_length_ms: float = (60_000 / bpm) / 2
	swing_ratio: float = 4 / 5

	swung: AudioSegment = AudioSegment.silent(0)

	i: int = 0
	while i < len(song):
		long_seg: AudioSegment = song[i:i + subdivision_length_ms]
		if len(long_seg) > 0:
			long_seg = stretch(long_seg, swing_ratio)
		swung += long_seg
		i += subdivision_length_ms

		short_seg: AudioSegment = song[i:i + subdivision_length_ms]
		if len(short_seg) > 0:
			short_seg = stretch(short_seg, swing_ratio ** -1)
		swung += short_seg
		i += subdivision_length_ms

	return swung
