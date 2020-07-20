#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from timeit import timeit

setup = """
import numpy as np
from numpy_ringbuffer import RingBuffer
from collections import deque

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from dvg_ringbuffer import RingBuffer as DvG_RingBuffer

np.random.seed(0)

N_buffers_passed = 100
buffer_size = 500
deque_size  = 20500

rb_dvg = DvG_RingBuffer(capacity=deque_size)
rb_numpy = RingBuffer(capacity=deque_size)
rb_deque = deque(maxlen=deque_size)

def mode_dvg():
    for i in range(N_buffers_passed):
        rb_dvg.extend(np.random.randn(buffer_size))

        if rb_dvg.is_full:
            c = rb_dvg[0:100]
            #d = np.asarray(rb_dvg)

            #print(c.__array_interface__['data'][0])

def mode_numpy():
    for i in range(N_buffers_passed):
        rb_numpy.extend(np.random.randn(buffer_size))

        if rb_numpy.is_full:
            c = rb_numpy[0:100]
            #d = np.asarray(rb_dvg)

            #print(c.__array_interface__['data'][0])

def mode_deque():
    for i in range(N_buffers_passed):
        rb_deque.extend(np.random.randn(buffer_size))

        if len(rb_deque) == rb_deque.maxlen:
            c = (np.array(rb_deque))[0:100]

            #print(c.__array_interface__['data'][0])

"""

N = 100
print("Feeding different ring buffers with data:")

print("  dvg_ringbuffer   : ", end="")
print("%.3f ms" % (timeit("mode_dvg()", setup=setup, number=N) / N * 1000))
print("  numpy_ringbuffer : ", end="")
print("%.3f ms" % (timeit("mode_numpy()", setup=setup, number=N) / N * 1000))
print("  deque (slow!)    : ", end="")
print("%.3f ms" % (timeit("mode_deque()", setup=setup, number=N) / N * 1000))
