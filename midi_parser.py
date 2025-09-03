from collections import deque
from dataclasses import dataclass
from mido import MidiFile as MidoFile, MidiTrack as MidoTrack, Message as MidoMessage
from os import path, PathLike
from typing import Self

__all__: list[str] = ['MidiData', 'MidiTrack', 'MidiNote']


@dataclass
class MidiNote:
	note: int
	start: int
	end: int


@dataclass
class MidiTrack:
	name: str
	notes: list[MidiNote]


@dataclass
class MidiData:
	name: str
	bpm: int
	tpb: int
	tracks: list[MidiTrack]

	@classmethod
	def parse(cls, file: PathLike | str) -> Self:
		midi: MidoFile = MidoFile(file)
		name: str = path.splitext(path.split(file)[1])[0]
		bpm: int = 120
		tpb: int = midi.ticks_per_beat
		tracks: list[MidiTrack] = []

		track: MidoTrack
		for track in midi.tracks:
			track_name: str = track.name
			track_notes: list[MidiNote] = []

			current_time: int = 0
			note_starts: dict[int, deque[int]] = {}
			msg: MidoMessage
			for msg in track:
				msg_data: dict = msg.dict()
				current_time += msg_data.get('time')

				match msg_data.get('type'):
					case 'track_name':
						track_name = msg_data.get('name')
					case 'set_tempo':
						bpm = 60_000_000 // msg_data.get('tempo')
					case 'note_on':
						note: int = msg_data.get('note')
						if note not in note_starts:
							note_starts[note] = deque()
						note_starts[note].append(current_time)
					case 'note_off':
						note: int = msg_data.get('note')
						start: int = note_starts.get(note).popleft()
						track_notes.append(MidiNote(note, start, current_time))

			tracks.append(MidiTrack(name=track_name, notes=track_notes))

		return cls(name=name, bpm=bpm, tpb=tpb, tracks=tracks)
