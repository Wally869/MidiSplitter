from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from glob import glob
import mido
from MidiStructurer.Instruments import InstrumentsLibrary

from copy import deepcopy
from numpy import array

from utils import FindExclusionThreshold, GetSelectedMessageTypes, GetSelectedMessageTypesInSong

from typing import List

import argparse


@dataclass
class PARAMETERS:
    InputFolder = "InputSplitter"
    OutputFolder = "OutputSplitter"
    MinimumMessages = 20
    TimeDeltaExclusionMultiplier = 5
    UseCorrectInstrument = True


# create a report on file splitted
# save some splitting parameters as well
class Report(object):
    def __init__(self):
        self.NbTracksBeforeSplit = 0
        self.NbTracksAfterSplit = 0
        self.NbSegmentsTotal = 0
        self.NbSegmentsKept = 0

        self.SegmentsInformation = []

    def CountTracksAfterSplit(self):
        tracksReported = set()
        for si in self.SegmentsInformation:
            tracksReported.add(si["Channel"])
        self.NbTracksAfterSplit = len(tracksReported)


    # incorrect nb of tracks after split
    def Stringify(self, filename):
        reportString = "Filename: " + filename + ".mid\n"
        for field in self.__dict__.keys():
            if field != "SegmentsInformation":
                reportString += "{}: {}\n".format(field, self.__dict__[field])
        reportString += "\n"
        reportString += "Minimum Messages: {}\n".format(PARAMETERS.MinimumMessages)
        reportString += "Exclusion Multiplier: {}\n".format(PARAMETERS.TimeDeltaExclusionMultiplier)
        reportString += "\n"
        for segmentInfo in self.SegmentsInformation:
            separator = "=" * 10 + "\n"
            reportString += separator
            reportString += "Channel: {}\n".format(segmentInfo["Channel"])
            if segmentInfo["Channel"] != 9:
                reportString += "Instrument: {}\n".format(segmentInfo["Instrument"])
            else:
                reportString += "Instrument: {}\n".format("Drums")
            reportString += "NbMessages: {}\n".format(segmentInfo["NbMessages"])
            reportString += "\n"
        return reportString



report = Report()

def main():
    allFiles = glob(PARAMETERS.InputFolder + "/*.mid")
    for f in allFiles:
        global report
        report = Report()
        HandleSong(f)



def HandleSong(filepath: str):
    f = mido.MidiFile(filepath)

    # get some metamessages and variables of interest
    tempoMessages = GetSelectedMessageTypesInSong(f, "set_tempo")
    tempoMessage = tempoMessages[0]
    ticksPerBeat = f.ticks_per_beat

    tracks = SplitSong(f)
    # set the tracks
    SaveSegments(filepath, tracks, ticksPerBeat, tempoMessage)


def SplitSong(song: mido.MidiFile) -> List[List[mido.message]]:
    # keep tracks with note_on
    report.NbTracksBeforeSplit = len(song.tracks)
    selectedTracks = list(
        filter(
            lambda x: HasNotes(x),
            song.tracks
        )
    )

    #report.NbTracksAfterSplit = len(selectedTracks)

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
def SaveSegments(filepath, segments, ticksPerBeat, tempoMessage):
    filename = filepath.replace(".mid", "")
    filename = filename.split("/")[-1]
    prefixesUsed = {}
    for t in segments:
        report.NbSegmentsTotal += 1
        # special case for drums
        if t[0] == 9:
            instrumentChannel = "Drums"
        else:
            instrumentChannel = InstrumentsLibrary.GetInstrumentFromSignal(t[1])
        currPrefix = "Track{}_{}".format(t[0], instrumentChannel)
        if currPrefix in prefixesUsed.keys():
            prefixesUsed[currPrefix] += 1
        else:
            prefixesUsed[currPrefix] = 1
        name = currPrefix + "-{}.mid".format(
            prefixesUsed[currPrefix] - 1
        )

        mf = mido.MidiFile()
        # adding a program_change to get correct sound
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
            report.NbSegmentsKept += 1
            report.SegmentsInformation.append(
                {
                    "Channel": t[0],
                    "Instrument": instrumentChannel,
                    "NbMessages": len(mf.tracks[0]) - 1
                }
            )
            outputpath = PARAMETERS.OutputFolder + "/" + filename
            Path(outputpath).mkdir(parents=True, exist_ok=True)
            mf.save(outputpath + "/" + name)

    report.CountTracksAfterSplit()
    stringReport = report.Stringify(filename)
    outputpath = PARAMETERS.OutputFolder + "/" + filename
    with open(outputpath + "/-----SplitterReport-----.txt", "w+") as f:
        f.write(stringReport)

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

# change outputfolder argparse to allow for multiple folders?
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split Midi Songs')
    parser.add_argument("-inputfolder", nargs="+", default="InputSplitter")
    parser.add_argument("-outputfolder", default="OutputSplitter")
    parser.add_argument("-minmessages", default=20, help="Prune tracks with less midi messages than this number")
    parser.add_argument("-exclusionmultiplier", default=5, help="Multiplier for timedelta messages. Median of timedelta multiplied by this determines section splitting")
    parser.add_argument("-useinstrumentsound", default=True, help="Use the track instrument, or default to Acoustic Grand Piano")

    args = parser.parse_args()

    #PARAMETERS.InputFolder = args.inputfolder
    PARAMETERS.OutputFolder = args.outputfolder
    PARAMETERS.MinimumMessages = args.minmessages
    PARAMETERS.TimeDeltaExclusionMultiplier = args.exclusionmultiplier
    PARAMETERS.UseCorrectInstrument = args.useinstrumentsound

    if type(args.inputfolder) != list:
        args.inputfolder = [args.inputfolder]

    for folder in args.inputfolder:
        PARAMETERS.InputFolder = folder
        main()
