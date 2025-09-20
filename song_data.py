from dataclasses import dataclass
from instrument import Instrument, load_instruments
from midi_parser import MidiData, MidiTrack, MidiNote
from os import PathLike
from typing import Self


@dataclass
class Note:
	note: int
	start: float
	end: float

	@classmethod
	def from_midi_note(cls, note: MidiNote, bpm: int, tpb: int) -> Self:
		tick_len: float = 60 / (bpm * tpb)

		return cls(
			note=note.note,
			start=note.start * tick_len,
			end=note.end * tick_len
		)


@dataclass
class Track:
	name: str
	instrument: Instrument
	notes: list[Note]

	@classmethod
	def from_midi_track(cls, track: MidiTrack, instrument: Instrument, bpm: int, tpb: int) -> Self:
		return cls(
			name=track.name,
			instrument=instrument,
			notes=[Note.from_midi_note(note, bpm, tpb) for note in track.notes]
		)


@dataclass
class Song:
	name: str
	island_id: int
	bpm: int
	tracks: list[Track]

	@property
	def length(self) -> float:
		end: float = 0

		for track in self.tracks:
			for note in track.notes:
				if note.end > end:
					end = note.end

		return end

	@classmethod
	def from_midi(cls, midi: MidiData, instrument_folder: PathLike | str) -> Self:
		# some risky shit here, but if bbb sticks to their goddamn scheme, it'll be fine
		# (knowing bbb they won't, i mean gold epic wubbox uses -s instead of _s in its track bin)
		island_id_str: str = midi.name.replace('world', '')
		island_id: int = int(island_id_str)
		instruments: list[Instrument] = load_instruments(instrument_folder, island_id)

		if len(island_id_str) >= 3:
			normal_id: int = int(island_id_str[1:])
			instruments += load_instruments(instrument_folder, normal_id, True)

		tracks: list[Track] = []

		midi_track: MidiTrack
		for midi_track in midi.tracks:
			track_instruments: list[Instrument] = [
				instrument for instrument in instruments
				if instrument.name == midi_track.name
			]

			if len(track_instruments) != 1:
				continue

			tracks.append(Track.from_midi_track(
				midi_track,
				track_instruments[0],
				midi.bpm,
				midi.tpb
			))

		tracks.sort(key=lambda track: track.name)

		return cls(
			name=midi.name,
			island_id=island_id,
			bpm=midi.bpm,
			tracks=tracks
		)