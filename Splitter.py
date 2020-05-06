from __future__ import annotations

from pathlib import Path
from glob import glob
import mido
from MidiStructurer.Instruments import Instruments

from copy import deepcopy
from numpy import array

from utils import FindExclusionThreshold, GetSelectedMessageTypes, GetSelectedMessageTypesInSong

from typing import List

import argparse

class PARAMETERS:
    InputFolder = "InputSplitter"
    OutputFolder = "OutputSplitter"
    MinimumMessages = 20
    TimeDeltaExclusionMultiplier = 5
    UseCorrectInstrument = True


def main():
    allFiles = glob(PARAMETERS.InputFolder + "/*.mid")
    for f in allFiles:
        HandleSong(f)



def HandleSong(filepath: str):
    f = mido.MidiFile(filepath)

    # get some metamessages and variables of interest
    tempoMessages = GetSelectedMessageTypesInSong(f, "set_tempo")
    tempoMessage = tempoMessages[0]
    ticksPerBeat = f.ticks_per_beat

    tracks = SplitSong(f)
    # set the tracks
    SaveTracks(filepath, tracks, ticksPerBeat, tempoMessage)


def SplitSong(song: mido.MidiFile) -> List[List[mido.message]]:
    # keep tracks with note_on
    selectedTracks = list(
        filter(
            lambda x: HasNotes(x),
            song.tracks
        )
    )

    # first, go through all messages for all tracks to get their timedelta
    # excluding timedeltas of 0
    timedeltas = ExtractTimedeltas(selectedTracks, True)
    timedeltas = array(timedeltas)
    timedeltas = timedeltas[timedeltas > 0.0]

    exclThreshold = FindExclusionThreshold(timedeltas, PARAMETERS.TimeDeltaExclusionMultiplier)

    # now for actual splitting
    tracks = []
    for t in selectedTracks:
        idT = FindIdTrack(t)
        tracks += SplitTrack(idT, t, exclThreshold)

    # prune non program_change or note messages
    tracks = [
        [
            t[0], t[1],
            GetSelectedMessageTypes(
                t[2],
                ["program_change", "note_on", "note_off"]
            )
        ] for t in tracks
    ]

    return tracks

# need to add translation from program to instrument name
def SaveTracks(filepath, tracks, ticksPerBeat, tempoMessage):
    filename = filepath.replace(".mid", "")
    filename = filename.split("/")[-1]
    prefixesUsed = {}
    for t in tracks:
        # special case for drums
        if t[0] == 9:
            instrumentChannel = "Drums"
        else:
            #print(t[1])
            instrumentChannel = Instruments.GetInstrumentFromSignal(t[1])
        currPrefix = "Track{}_{}".format(t[0], instrumentChannel)
        if currPrefix in prefixesUsed.keys():
            prefixesUsed[currPrefix] += 1
        else:
            prefixesUsed[currPrefix] = 1
        name = currPrefix + "-{}.mid".format(
            prefixesUsed[currPrefix] - 1
        )

        mf = mido.MidiFile()
        # adding a program_change to get correct sound?
        if PARAMETERS.UseCorrectInstrument:
            if t[0] != 9:
                if t[1] < 0:
                    print("Error on instrument in track {}".format(t[0]))
                    t[1] = max(0, t[1])
                instrumentMessage = mido.Message(
                    type="program_change",
                    program=t[1],
                    channel=t[0]
                )
                mf.tracks = [[instrumentMessage, tempoMessage] + t[2]]
            else:
                mf.tracks = [[tempoMessage] + t[2]]
        else:
            mf.tracks = [[tempoMessage] + t[2]]
        mf.ticks_per_beat = ticksPerBeat

        # aaaand save file pog
        # moved the length check here, seemed to have issues before?
        if len(mf.tracks[0]) > PARAMETERS.MinimumMessages:
            outputpath = PARAMETERS.OutputFolder + "/" + filename
            Path(outputpath).mkdir(parents=True, exist_ok=True)
            mf.save(outputpath + "/" + name)


def FindIdTrack(track):
    for m in track:
        if m.type == "note_on":
            return m.channel
    return -1

def HasNotes(track):
    for m in track:
        if m.type == "note_on":
            return True
    return False


def ExtractTimedeltas(tracks, excludeZero: bool = True):
    timedeltas = []
    for t in tracks:
        for m in t:
            if m.time != 0 and excludeZero:
                timedeltas.append(m.time)
            else:
                timedeltas.append(m.time)
    return timedeltas


def SplitTrack(idTrack, trackMessages, exclThreshold) -> List[List[mido.message]]:
    outTracks = []

    # check for program change and timedelta > exclThreshold
    # to split the track
    currIdInstrument = -1
    # expecting program_change message to be the first valid message
    currTrack = []
    for msg in trackMessages:
        # first, try to find instrument for track
        if msg.type == "program_change":
            if currIdInstrument < 0:
                currIdInstrument = msg.program
            else:
                # if already have instrument, new instrument and save previous track
                if len(currTrack) > 0:
                    outTracks.append((idTrack, currIdInstrument, currTrack))
                    msg.time = 0
                    currTrack = [msg]
                    currIdInstrument = msg.program
        elif msg.time > exclThreshold:
            # if same instrument, but too long time in between events
            outTracks.append((idTrack, currIdInstrument, currTrack))
            msg.time = 0
            currTrack = [msg]
        else:
            currTrack.append(msg)

    outTracks.append((idTrack, currIdInstrument, currTrack))

    return outTracks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split Midi Songs')
    parser.add_argument("-inputfolder", default="InputSplitter")
    parser.add_argument("-outputfolder", default="OutputSplitter")
    parser.add_argument("-minmessages", default=20)
    parser.add_argument("-exclusionmultiplier", default=5)
    parser.add_argument("-useinstrumentsound", default=True)

    args = parser.parse_args()

    PARAMETERS.InputFolder = args.inputfolder
    PARAMETERS.OutputFolder = args.outputfolder
    PARAMETERS.MinimumMessages = args.minmessages
    PARAMETERS.TimeDeltaExclusionMultiplier = args.exclusionmultiplier
    PARAMETERS.UseCorrectInstrument = args.useinstrumentsound

    main()