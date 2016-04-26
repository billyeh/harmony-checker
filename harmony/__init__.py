import sys
from music21 import *

def _diatonicInterval(p1, p2):
  generic = interval.notesToGeneric(p1, p2)
  chromatic = interval.notesToChromatic(p1, p2)
  return interval.intervalsToDiatonic(generic, chromatic)

def Spacing(prev, curr, next):
  """Intervals between adjacent voices should be no bigger than an octave,
  bass excepted.

  >>> Spacing(None, chord.Chord(['C2', 'G1', 'E1', 'C1']), None)
  True
  >>> Spacing(None, chord.Chord(['C2', 'E2', 'D2', 'C1']), None)
  True
  >>> Spacing(None, chord.Chord(['C2', 'E2', 'C1', 'C1']), None)
  False
  """

  for i in range(2):
    p1, p2 = (curr.pitches[i], curr.pitches[i+1])
    dist = abs(interval.notesToGeneric(p1, p2).staffDistance)
    if dist > 7:
      return False
  return True

def HasThird(prev, curr, next):
  """Every chord should have a third.

  >>> HasThird(None, chord.Chord(['G3', 'G2', 'C2', 'C1']), None)
  False
  >>> HasThird(None, chord.Chord(['G3', 'C2', 'E1', 'C1']), None)
  True
  """

  return bool(curr.third)

def VocalRanges(prev, curr, next):
  """Each voice should sing a pitch within their range.

  >>> VocalRanges(None, chord.Chord(['C4', 'C3', 'C2', 'C1']), None)
  False
  >>> VocalRanges(None, chord.Chord(['C5', 'G3', 'G4', 'C4']), None)
  True
  """

  ranges = [('C4', 'G5'), ('G3', 'D5'), ('C3', 'G4'), ('D2', 'C4')]
  pitches = curr.pitches
  for i, r in enumerate(ranges):
    if pitches[i] < pitch.Pitch(r[0]) or pitches[i] > pitch.Pitch(r[1]):
      return False
  return True

def VoiceCrossing(prev, curr, next):
  """No voice should sing a note above the voice above it.

  >>> VoiceCrossing(None, chord.Chord(['C4', 'C3', 'C2', 'C1']), None)
  True
  >>> VoiceCrossing(None, chord.Chord(['C3', 'C4', 'C2', 'C1']), None)
  False
  """

  for i in range(3):
    if curr.pitches[i] < curr.pitches[i+1]:
      return False
  return True

def VoiceOverlap(prev, curr, next):
  """No voice should go above the note previously sang by the voice above it.
  No voice should go below the note previously sang by the voice below it.

  >>> VoiceOverlap(chord.Chord(['C2', 'C2', 'C2', 'C1']), \
      chord.Chord(['C2', 'C2', 'C2', 'C3']), None)
  False
  >>> VoiceOverlap(chord.Chord(['C4', 'C3', 'C2', 'C1']), \
      chord.Chord(['B4', 'B3', 'B2', 'B1']), None)
  True
  """

  if not prev:
    return True
  for i in range(3):
    if curr.pitches[i+1] > prev.pitches[i]:
      return False
  for i in range(3):
    if curr.pitches[i] < prev.pitches[i+1]:
      return False
  return True

def FirstAndLastChord(prev, curr, next):
  """First chord needs to be complete and double the root. Last chord needs to
  either be the same, or omit the fifth and triple the root.

  >>> c1 = chord.Chord(['C1', 'E1', 'G1', 'C2'])
  >>> c1.key = key.Key('C')
  >>> FirstAndLastChord(None, c1, None)
  True
  >>> c2 = chord.Chord(['C2', 'E1', 'C1', 'C1'])
  >>> c2.key = key.Key('C')
  >>> FirstAndLastChord(None, c2, None)
  False
  >>> FirstAndLastChord(c1, c1, c1)
  True
  >>> FirstAndLastChord(c1, c2, None)
  True
  """

  complete_doubled_root = lambda d: d.count(1) == 2 and d.count(3) == 1 and \
      d.count(5) == 1
  degrees = list(map(lambda x: x[0], curr.scaleDegrees))
  if not prev:
    return complete_doubled_root(degrees)
  if not next:
    return (degrees.count(1) == 3 and degrees.count(3) == 1) or \
        complete_doubled_root(degrees)
  return True

def ResolveLeadingTone(prev, curr, next):
  """Leading tone leads to tonic in the next chord

  >>> c1 = chord.Chord(['G1', 'B1', 'D1', 'G2'])
  >>> c1.key = key.Key('C'); c1.lyric = 'V'
  >>> c2 = chord.Chord(['C1', 'C2', 'E2', 'G2'])
  >>> c2.key = key.Key('C'); c2.lyric = 'V'
  >>> ResolveLeadingTone(None, c1, c2)
  True
  >>> c3 = chord.Chord(['C1', 'D2', 'E2', 'G2'])
  >>> c3.key = key.Key('C'); c2.lyric = 'V'
  >>> ResolveLeadingTone(None, c1, c3)
  False
  """

  if not next:
    return True
  currDegrees = list(map(lambda x: x[0], curr.scaleDegrees))
  nextDegrees = list(map(lambda x: x[0], next.scaleDegrees))
  for i in range(4):
    if currDegrees[i] == 7:
      if curr.key.mode == 'major' and nextDegrees[i] != 1:
        return False
      p = curr.pitches[i]
      if curr.key.mode == 'minor' and nextDegrees[i] != 1 and \
          p.accidental and p.accidental.name == 'sharp':
        return False
  return True

def ResolveSevenths(prev, curr, next):
  """The seventh of the chord must resolve down by a step

  >>> c1 = chord.Chord(['c', 'e', 'g', 'b-'])
  >>> c2 = chord.Chord(['f', 'a', 'c', 'a'])
  >>> ResolveSevenths(None, c1, c2)
  True
  >>> c3 = chord.Chord(['f', 'a', 'c', 'f'])
  >>> ResolveSevenths(None, c1, c3)
  False
  """

  if not next:
    return True
  for i in range(4):
    if curr.pitches[i] == curr.seventh:
      m2 = interval.notesToGeneric(note.Note('c'), note.Note('b'))
      M2 = interval.notesToGeneric(note.Note('g'), note.Note('f'))
      return interval.notesToGeneric(curr.pitches[i], next.pitches[i]) in [m2, M2]
  return True

def PrepareSevenths(prev, curr, next):
  """If possible, the seventh of the chord must be held over from the same 
  voice in the previous chord

  >>> c1 = chord.Chord(['F1', 'A1', 'C2', 'F2'])
  >>> c2 = chord.Chord(['G1', 'F1', 'D2', 'B2'])
  >>> PrepareSevenths(c1, c2, None)
  False
  >>> c3 = chord.Chord(['G1', 'B1', 'D2', 'F2'])
  >>> PrepareSevenths(c1, c3, None)
  True
  """

  if not prev:
    return True
  for i in range(4):
    if curr.pitches[i] == curr.seventh:
      if not curr.pitches[i].name in prev.pitchNames:
        return True
      return prev.pitches[i] == curr.pitches[i]
  return True

def NoAugmentedSecond(prev, curr, next):
  """Don't make anyone sing an augmented 2nd!

  >>> c1 = chord.Chord(['C1', 'C2', 'C3', 'C4'])
  >>> c2 = chord.Chord(['D#1', 'C2', 'C3', 'C4'])
  >>> NoAugmentedSecond(c1, c2, None)
  False
  >>> NoAugmentedSecond(c1, c1, None)
  True
  """

  if not prev:
    return True
  for i in range(4):
    full = _diatonicInterval(curr.pitches[i], prev.pitches[i])
    if full.name == 'A2':
      return False
  return True

def ParallelOctavesFifthsUnisons(prev, curr, next):
  """Voices moving in parallel 5ths, 8ves, or 1sts are bad.

  >>> c1 = chord.Chord(['C1', 'C2', 'C3', 'C4'])
  >>> c2 = chord.Chord(['G1', 'G2', 'C3', 'C4'])
  >>> ParallelOctavesFifthsUnisons(c1, c2, None)
  False
  >>> c3 = chord.Chord(['C1', 'D2', 'C3', 'C4'])
  >>> ParallelOctavesFifthsUnisons(c1, c3, None)
  True
  """

  if not prev:
    return True
  parallels = ['P8', 'P5', 'P1']
  for i in range(4):
    for j in range(4):
      if i == j:
        continue
      full = _diatonicInterval(curr.pitches[i], curr.pitches[j])
      if not full.name in parallels:
        continue
      if curr.pitches[i] == prev.pitches[i] and \
          curr.pitches[j] == prev.pitches[j]: #notes didn't change
        return True
      if _diatonicInterval(prev.pitches[i], prev.pitches[j]).name == full.name:
        return False
  return True

def HiddenOctavesAndFifths(prev, curr, next):
  """Voices moving in similar motion should not end up on fifths or octaves

  >>> c1 = chord.Chord(['C2', 'G1', 'E1', 'C1'])
  >>> c2 = chord.Chord(['E2', 'A1', 'E1', 'C1'])
  >>> HiddenOctavesAndFifths(c1, c2, None)
  False
  >>> c3 = chord.Chord(['D2', 'G1', 'G2', 'C1'])
  >>> HiddenOctavesAndFifths(c1, c3, None)
  True
  """

  if not prev:
    return True
  for i in range(4):
    for j in range(4):
      firstInt = interval.notesToGeneric(prev.pitches[i],
          curr.pitches[i]).staffDistance
      secondInt = interval.notesToGeneric(prev.pitches[j],
          curr.pitches[j]).staffDistance
      if firstInt == 0 or secondInt == 0:
        continue
      sign = lambda x: (1, -1)[x<0]
      if sign(firstInt) == sign(secondInt) and firstInt != secondInt:
        resultInt = interval.notesToGeneric(curr.pitches[i], 
            curr.pitches[j]).staffDistance
        if abs(resultInt) in [7, 4]:
          return False
  return True

def NoRootDiminishedChords(prev, curr, next):
  """We don't allow root-position diminished chords

  >>> c = chord.Chord(['c', 'e-', 'g-', 'b--'])
  >>> NoRootDiminishedChords(None, c, None)
  False
  >>> c = chord.Chord(['c', 'e-', 'g-'])
  >>> NoRootDiminishedChords(None, c, None)
  False
  >>> c.inversion(1)
  >>> NoRootDiminishedChords(None, c, None)
  True
  """

  if curr.quality == 'diminished' and curr.inversion() == 0:
    return False
  return True

def SevenSevenChordResolved(prev, curr, next):

  return True

rules = [
  Spacing, 
  HasThird,
  VocalRanges,
  VoiceCrossing,
  VoiceOverlap,
  FirstAndLastChord,
  ResolveLeadingTone,
  ResolveSevenths,
  PrepareSevenths,
  NoAugmentedSecond,
  ParallelOctavesFifthsUnisons,
  HiddenOctavesAndFifths,
  NoRootDiminishedChords,
  SevenSevenChordResolved
]

def run_tests():
  print('Testing module...')
  import doctest
  doctest.testmod()

def analyze_file(data):
  print('Analyzing music...')
  errors = []
  s = converter.parseData(data)
  key = s.analyze('key')
  sChords = s.chordify(addPartIdAsGroup=True)
  chords = [None]
  for c in sChords.recurse(classFilter='Chord'):
    rn = roman.romanNumeralFromChord(c, key)
    c.addLyric(str(rn.figure))
    c.key = key
    chords.append(c)
  chords.append(None)
  for i, c in enumerate(chords[1:-1]):
    prev, curr, next = chords[i:i+3]
    for rule in rules:
      if not rule(prev, curr, next):
        errors.append(rule.__name__ + ' failed for chord ' + str(i+1))
  if not errors:
    errors.append('No errors')
  return Report(errors, chords[1:-1])

class Report:
  def __init__(self, errors, chords):
    self.errors = errors
    self.chords = []
    k = chords[0].key if chords else 'C'
    keyPitches = k.getPitches(pitch.Pitch('C1'), pitch.Pitch('C8'))
    for c in chords:
      cObj = []
      for p in c.pitches:
        cObj.append({
          'key': '/'.join((str(p.step), str(p.octave))),
          'displayAcc': p not in keyPitches,
          'accidental': p.accidental.modifier if p.accidental else ''
        })
      self.chords.append({'notes': cObj, 'roman': c.lyric})
    self.key = k.tonicPitchNameWithCase
    if self.key[0].islower():
      self.key = self.key[0].upper() + 'm' + self.key[1:]

def main():
  if len(sys.argv) == 1:
    run_tests()
  else:
    data = open(sys.argv[1]).read()
    report = analyze_file(data)
    print(report.errors)
  print('Done!')

if __name__ == '__main__':
  main()

