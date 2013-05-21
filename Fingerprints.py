#!/usr/bin/python
from datetime import datetime
from itertools import combinations, dropwhile
from math import ceil
from os.path import join
from random import seed, shuffle
from sys import argv

try:
    from pygame import init as pyGameInit
    from pygame import Surface
    from pygame import NOFRAME
    from pygame import BLEND_MIN, BLEND_ADD
    from pygame.display import set_mode
    from pygame.image import load, save, get_extended
    #from pygame.transform import flip
    from pygame.transform import smoothscale
except ImportError, ex:
    raise ImportError("%s: %s\n\nPlease install PyGame v1.9.1 or later: http://pygame.org\n" % (ex.__class__.__name__, ex))

try:
    from pygame.font import SysFont
except ImportError, ex:
    SysFont = None
    print "\nWARNING: pygame.font cannot be imported, text information will not be available"

assert get_extended()

PROGRAM_NAME = 'Fingerprints.py'

EXTENSION = 'png'

TITLE = "Fingerprints for Games Generator"

USAGE_INFO = """Usage:
python %s generate - Create initial sequence file.
python %s <filename> <mask> - Create fingerprints sheet for the specified mask and save it to filename.%s.
python %s <fileName> - Create fingeprints sheets for all masks in the specified sequence file.""" % (PROGRAM_NAME, PROGRAM_NAME, EXTENSION, PROGRAM_NAME)

SEED = 518

N = 14 # Number of possible elements in a fingerprint
K = 7  # Number of elements on a person's fingerprint

NPLAYERS = 200

DPI = 300
DPC = DPI / 2.54

PAGE_WIDTH = int(29.7 * DPC)
PAGE_HEIGHT = int(21 * DPC)

FIELD = 3

NCOLUMNS = 8
NROWS = 4

SAMPLES = ((7, 4), (5, 2), (4, 7), (3, 10), (2, 7), (1, 2))
assert sum(nFingers for (nSamples, nFingers) in SAMPLES) == NCOLUMNS * NROWS
BLANK_SAMPLES = ((N, NROWS * NCOLUMNS),)

CELL_WIDTH = int((PAGE_WIDTH - FIELD) // NCOLUMNS)
CELL_HEIGHT = int((PAGE_HEIGHT - FIELD) // NROWS)

BACKGROUND_COLOR = (255, 255, 255) # white
MASK_COLOR = (178, 178, 178) # gray
FULL_COLOR = BACKGROUND_COLOR # white
PART_COLOR = (0, 0, 0) # black
FONT_NAMES = ('Verdana', 'Arial', None)

TITLE_POSITION = (int(0.3 * DPC), int(0.25 * DPC))
FONT_SIZE = int(0.3 * DPC)

BASE_CHAR = 'A'
BACK_CHAR = '@'
FULL_CHAR = '$'
PART_CHAR = '&'
MASK_CHAR = '#'

LAYERS = ''.join(chr(ord(BASE_CHAR) + i) for i in xrange(N))
ALL_LAYERS = BACK_CHAR + FULL_CHAR + PART_CHAR + MASK_CHAR + LAYERS

layers = {}
font = None

assert PAGE_WIDTH >= CELL_WIDTH
assert PAGE_HEIGHT >= CELL_HEIGHT

def createSequence():
    masks = [''.join(c) for c in combinations(LAYERS, K)]
    length = len(masks)
    print '# %s' % TITLE
    print '# N=%d  K=%d  C=%d  P=%d  S=%d   Created at %s' % (N, K, length, NPLAYERS, SEED, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print 'blank ' + LAYERS
    seed(SEED)
    shuffle(masks)
    for (name, mask) in zip(xrange(1, NPLAYERS + 1), masks):
        print '%%0%dd %%s' % len(str(NPLAYERS)) % (name, mask)

def getFileName(n):
    return '%s.%s' % (n, EXTENSION)

def initGraphics():
    print '\n%s\n' % TITLE
    pyGameInit()
    set_mode((1, 1), NOFRAME)
    for n in ALL_LAYERS:
        layers[n] = smoothscale(load(join('Layers', getFileName(n))), (CELL_WIDTH, CELL_HEIGHT))
    global font # pylint: disable=W0603
    font = dropwhile(lambda font: not font, (SysFont(fontName, FONT_SIZE, bold = True) for fontName in FONT_NAMES)).next() if SysFont else None

def createFinger(mask, name = ''):
    finger = Surface((CELL_WIDTH, CELL_HEIGHT)) # pylint: disable=E1121
    finger.fill(BACKGROUND_COLOR)
    for m in mask + (MASK_CHAR if len(mask) > K else '') + BACK_CHAR + (MASK_CHAR if len(mask) > K else FULL_CHAR if len(mask) == K else PART_CHAR):
        finger.blit(layers[m], (0, 0), special_flags = BLEND_ADD if m == MASK_CHAR else BLEND_MIN)
    if font:
        finger.blit(font.render(name or u' \u0411', True, MASK_COLOR if len(mask) > K else FULL_COLOR if len(mask) == K else PART_COLOR), TITLE_POSITION) # using russian 'B' to indicate proper viewing position
    return finger

def createSheet(name, mask):
    fileName = getFileName(name)
    print '%s -> %s' % (mask, fileName)
    fileName = join('Result', fileName)
    sheet = Surface((PAGE_WIDTH, PAGE_HEIGHT)) # pylint: disable=E1121
    sheet.fill(BACKGROUND_COLOR)
    if name.isdigit():
        fullFingers = []
        partFingers = []
        seed((int(name) + 1) * SEED)
        for (nSamples, nFingers) in SAMPLES:
            samples = [''.join(c) for c in combinations(mask, nSamples)]
            shuffle(samples)
            samples = (samples * int(ceil(float(nFingers) / len(samples))))[:nFingers]
            samples = (createFinger(sample, name if i == 0 and nSamples >= K else '') for (i, sample) in enumerate(samples))
            (fullFingers if nSamples >= K else partFingers).extend(samples)
        shuffle(partFingers)
        fingers = fullFingers + partFingers
    else:
        fingers = (createFinger(mask),) * NROWS * NCOLUMNS
    assert len(fingers) <= NROWS * NCOLUMNS
    x = y = 0
    for (i, finger) in enumerate(fingers, 1):
        sheet.blit(finger, (x, y))
        if i % NROWS == 0:
            y = 0
            x += CELL_WIDTH
        else:
            y += CELL_HEIGHT
    #if name.isdigit():
    #    sheet = flip(sheet, True, False) # for printing backwards on transparent film
    save(sheet, fileName)

def createSheets(fileName):
    fileLines = (line.strip() for line in open(fileName))
    lines = (line for line in fileLines if line and not line.startswith('#'))
    for (name, mask) in (line.split() for line in lines):
        createSheet(name, mask)

def main(*args):
    if len(args) == 2:
        if args[1].lower() == 'generate':
            createSequence()
        else:
            initGraphics()
            createSheets(args[1])
    elif len(args) == 3:
        initGraphics()
        createSheet(args[1], args[2])
    else:
        print '\nERROR: Bad parameters\n\n%s\n' % USAGE_INFO

if __name__ == '__main__':
    main(*argv)
