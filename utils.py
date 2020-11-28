from __future__ import annotations
from typing import List

import mido
import numpy as np
from numpy import median

from copy import deepcopy


# Find threshold to exclude timedeltas outliers
def FindExclusionThreshold(arr: np.ndarray, cutoffMultiplier: float = 4) -> int:
    return int(median(arr) * cutoffMultiplier)



def GetSelectedMessageTypes(track: mido.MidiTrack,
                            allowedTypes: List[str] = ["note_on", "note_off"]
                            ) -> List[mido.Message]:
    return list(
        filter(
            lambda x: x.type in allowedTypes,
            track
        )
    )

def GetSelectedMessageTypesInSong(song: mido.MidiFile,
                            allowedTypes: List[str] = ["note_on", "note_off"]
                            ) -> List[mido.Message]:
    messages = [list(
        filter(
            lambda x: x.type in allowedTypes,
            track
        )
    ) for track in song.tracks]
    outMessages = []
    for m in messages:
        outMessages += m
    return outMessages


def MessageTimeToAbsolute(track: mido.MidiTrack):
    # time attribute for messages is the difference in tick between messages
    # this function computes absolute time for all messages
    time = 0
    outTrack = deepcopy(track)
    for msg in outTrack:
        time += msg.time
        msg.time = time
    return outTrack
