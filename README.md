# MidiSplitter

### Overview

Script to split midi files into tracks and subsegments.



### Dependencies

from pip: glob, mido, numpy 

from github: MidiStructurer (my repo: https://github.com/Wally869/MidiStructurer)



### Usage

Can be called directly from cmd

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
  -inputfolder INPUTFOLDER
  -outputfolder OUTPUTFOLDER
  -minmessages MINMESSAGES
                        Prune tracks with less midi messages than this number
  -exclusionmultiplier EXCLUSIONMULTIPLIER
                        Multiplier for timedelta messages. Median of timedelta
                        multiplied by this determines section splitting
  -useinstrumentsound USEINSTRUMENTSOUND
                        Use the track instrument, or default to Acoustic Grand
                        Piano
```



### Output

An input file of name "test.mid" will be output in a serie of mid files using the following naming scheme:

Track{TrackID}_{TrackInstrument}-{SectionID}.mid



To Note: some segments can be excluded so SectionID is not guaranteed to be continuous
