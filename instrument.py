from dataclasses import dataclass
from os import PathLike, path
from pathlib import Path
from struct import unpack
from typing import BinaryIO, Self
import re

__all__: list[str] = ['Instrument', 'load_instruments']


@dataclass
class Instrument:
	name: str
	tracks: dict[int, str]

	@classmethod
	def parse(cls, file: PathLike | str) -> Self:
		def read_string(f: BinaryIO) -> str:
			string_len: int = unpack('<I', f.read(4))[0] - 1  # null terminator, even bbb does this
			string: str = f.read(string_len).decode('ascii')
			f.seek(4 - (string_len % 4), 1)
			return string

		with open(file, 'rb') as fp:
			read_string(fp)
			fp.seek(4, 1)

			name: str = read_string(fp)

			read_string(fp)
			read_string(fp)
			fp.seek(8, 1)

			tracks: dict[int, str] = {}
			num_tracks: int = unpack('<I', fp.read(4))[0]
			for _ in range(num_tracks):
				note: int = unpack('<I', fp.read(4))[0] ^ 0x0000FF00
				audio: str = path.splitext(path.split(read_string(fp))[1])[0] + '.wav'
				fp.seek(4, 1)
				tracks[note] = audio

		return cls(name, tracks)


def load_instruments(folder: PathLike | str, island_id: int, skip_paironormals: bool = False) -> list[Instrument]:
	instruments: list[Instrument] = []

	file: Path
	for file in Path(folder).rglob(f'{str(island_id).zfill(3)}[_,-][A-Za-z0-9]*.bin'):
		file_str: str = str(file).lower()
		if ((
			skip_paironormals and
			re.match(r'\d{3}_I\d{2}.bin', path.split(file_str)[1]) is not None
		) or (
			'prop' in file_str and
			'finale' not in file_str
		) or (
			'phase' in file_str and
			'phase5' not in file_str
		)): continue

		try:
			instruments.append(Instrument.parse(file))
		except Exception as e:
			print(f'Failed to load instrument {file}: {e}')
			continue

	return instruments
