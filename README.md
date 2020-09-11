# MidiSplitter

### Overview

Script to split midi files from a folder, into subsegments.
The intent is to extract "patterns" from individual tracks


### Dependencies

from pip: glob, mido, numpy 

from github: MidiStructurer (my repo: https://github.com/Wally869/MidiStructurer)



### Usage

Can be called directly from cmd
the inputfolder argument can take lists so it is possible to operate on multiple folders at once

```
# No args
python Splitter.py

# see argparse parameters
python Splitter.py -h 
usage: Splitter.py [-h] [-inputfolder INPUTFOLDER]
                   [-outputfolder OUTPUTFOLDER] [-minmessages MINMESSAGES]
                   [-exclusionmultiplier EXCLUSIONMULTIPLIER]
                   [-useinstrumentsound USEINSTRUMENTSOUND]

Split Midi Songs

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTFOLDER [INPUTFOLDER ..]
  -o OUTPUTFOLDER
  -m MINMESSAGES
      Prune tracks with less midi messages than this number
  -e EXCLUSIONMULTIPLIER
      Multiplier for timedelta messages. Median of timedelta
      multiplied by this determines section splitting
  -u USEINSTRUMENTSOUND
      Use the track instrument, or default to Acoustic Grand Piano
```



### Output

An input file of name "test.mid" will be output in a serie of mid files using the following naming scheme:

Track{TrackID}_{TrackInstrument}-{SectionID}.mid

A report is also generated per song under the name "-----SplitterReport-----.txt".
It tracks some metrics, such as number of tracks before/after split, total number of segments,
number of segments kept.

It also records parameters used when splitting, and gives a breakdown of the segments recorded

To Note: some segments can be excluded so SectionID is not guaranteed to be continuous

A sample report:
```text
Filename: InputSplitter\test.mid
NbTracksBeforeSplit: 22
NbTracksAfterSplit: 12
NbSegmentsTotal: 46
NbSegmentsKept: 25

Minimum Messages: 20
Exclusion Multiplier: 5

==========
Channel: 0
Instrument: Acoustic Grand Piano
NbMessages: 703

==========
Channel: 1
Instrument: Acoustic Grand Piano
NbMessages: 198

==========
Channel: 2
Instrument: Acoustic Grand Piano
NbMessages: 503

```

### To Do

- Better threshold selection than naive full-song median multiplication, and do it by channel
- Implement threading (writing midi can be bottleneck I guess? Or handle songs seperately)
- Fix errors whenever possible
