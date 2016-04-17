#!/usr/bin/env python

## recordtest.py
##
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm forsound capture. Set
## various attributes of the capture, and reads in a loop,
## writing the data to standard out.
##
## To test it out do the following:
## python recordtest.py out.raw # talk to the microphone
## aplay -r 8000 -f S16_LE -c 1 out.raw

#!/usr/bin/env python

from __future__ import print_function

import sys
import alsaaudio
from numpy.fft import fft
import numpy
import matplotlib.pyplot as plt

def usage():
    print('usage: recordtest.py [-c <card>] <file>', file=sys.stderr)
    sys.exit(2)

if __name__ == '__main__':

    card = 'default'

    #opts, args = getopt.getopt(sys.argv[1:], 'c:')

    #if not args:
        #usage()

    #f = open(args[0], 'wb')

    # Open the device in nonblocking capture mode. The last argument could
    # just as well have been zero for blocking mode. Then we could have
    # left out the sleep call in the bottom of the loop
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, card)

    # Set attributes: Mono, 44100 Hz, 16 bit little endian samples
    inp.setchannels(1)
    inp.setrate(44100)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

    # The period size controls the internal number of frames per period.
    # The significance of this parameter is documented in the ALSA api.
    # For our purposes, it is suficcient to know that reads from the device
    # will return this many frames. Each frame being 2 bytes long.
    # This means that the reads below will return either 320 bytes of data
    # or 0 bytes of data. The latter is possible because we are in nonblocking
    # mode.
    inp.setperiodsize(160)

    loops = 5000000
    arr = numpy.zeros(loops)
    count = 0
    indices = numpy.array(range(160))
    for i in range(loops):
        # Read data from device
        l, data = inp.read()
        if l:
            window = numpy.fromstring(data, dtype=numpy.int16)
            x = fft(window)
            arr[count] = max(indices, key=lambda idx: x[idx])
            print(arr[count])
            count += 1

plt.plot(range(count), arr[:count], 'ro')
plt.axis([0, count, 0, int(max(arr) * 1.5)])
plt.show()
