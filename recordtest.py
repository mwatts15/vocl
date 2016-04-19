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
import threading
import alsaaudio
from numpy.fft import fft
import numpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time


def usage():
    print('usage: recordtest.py [-c <card>] <file>', file=sys.stderr)
    sys.exit(2)


if __name__ == '__main__':
    import signal
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
    PERIOD_SIZE = 160
    WINDOW_SIZE = 100
    THRESHOLD = 180000
    inp.setperiodsize(PERIOD_SIZE)

    loops = 5000000
    arr = numpy.zeros(loops)
    view_window = numpy.zeros(WINDOW_SIZE)
    view_window_indices = numpy.array(range(WINDOW_SIZE))
    count = [0]
    indices = numpy.array(range(PERIOD_SIZE))

    count_lock = threading.Lock()
    arr_lock = threading.Lock()

    should_stop = [False]

    def get_count():
        count_lock.acquire()
        v = count[0]
        count_lock.release()
        return v

    def set_count(v):
        count_lock.acquire()
        count[0] = v
        count_lock.release()

    def gather_data():
        while not should_stop[0]:
            # Read data from device
            l, data = inp.read()
            if l:
                window = numpy.fromstring(data, dtype=numpy.int16)
                x = fft(window)
                c = get_count()
                z = max(indices, key=lambda idx: x[idx])
                if x[z] >= THRESHOLD:
                    arr[c] = z
                    set_count(c + 1)

    fig1 = plt.figure()
    l, = plt.plot(range(get_count()), arr[:get_count()], 'ro')

    def update(num, l):
        length = view_window.shape[0]
        c = get_count()
        view_window[max(length - c, 0):] = arr[max(0, c - length): c]
        l.set_data(view_window_indices, view_window)
        return l,

    t = threading.Thread(target=gather_data)
    t.start()

    plt.axis([0, view_window.shape[0], 0, 100])
    plt.ion()

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        should_stop[0] = True
        t.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to stop the program')

    i = 0
    while True:
        update(i, l)
        plt.draw()
        plt.pause(.001)
        i += 1

