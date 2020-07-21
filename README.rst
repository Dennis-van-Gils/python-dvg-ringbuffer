.. image:: https://img.shields.io/pypi/v/dvg-ringbuffer
    :target: https://pypi.org/project/dvg-ringbuffer
.. image:: https://img.shields.io/pypi/pyversions/dvg-ringbuffer
    :target: https://pypi.org/project/dvg-ringbuffer
.. image:: https://travis-ci.org/Dennis-van-Gils/python-dvg-ringbuffer.svg?branch=master
    :target: https://travis-ci.org/Dennis-van-Gils/python-dvg-ringbuffer
.. image:: https://coveralls.io/repos/github/Dennis-van-Gils/python-dvg-ringbuffer/badge.svg?branch=master
    :target: https://coveralls.io/github/Dennis-van-Gils/python-dvg-ringbuffer?branch=master
.. image:: https://requires.io/github/Dennis-van-Gils/python-dvg-ringbuffer/requirements.svg?branch=master
    :target: https://requires.io/github/Dennis-van-Gils/python-dvg-ringbuffer/requirements/?branch=master
    :alt: Requirements Status
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/License-MIT-purple.svg
    :target: https://github.com/Dennis-van-Gils/python-dvg-ringbuffer/blob/master/LICENSE.txt

DvG_RingBuffer
==============
Numpy ring buffer at a *fixed* memory address to allow for significantly
sped up ``numpy``, ``sigpy``, ``numba`` & ``pyFFTW``  calculations.

**Based on:**
    https://pypi.org/project/numpy_ringbuffer/ by Eric Wieser.

    ``DvG_RingBuffer`` can be used as a drop-in replacement for
    ``numpy_ringbuffer`` and provides several optimizations and extra features,
    but requires Python 3.

If, and only if the ring buffer is completely full, will it return its array
data as a contiguous C-style numpy array at a single fixed memory address per
ring buffer instance. It does so by unwrapping the discontiguous ring buffer
array into a second extra *unwrap* buffer that is a private member of the ring
buffer class. This is advantegeous for other accelerated computations by, e.g.,
``numpy``, ``sigpy``, ``numba`` & ``pyFFTW``, that benefit from being fed with
contiguous arrays at the same memory address each time again, such that compiler
optimizations and data planning are made possible.

When the ring buffer is not completely full, it will return its data as a
contiguous C-style numpy array, but at different memory addresses. This is how
the original ``numpy-buffer`` always operates.

Commonly, ``collections.deque()`` is used to act as a ring buffer. The
benefits of a deque is that it is thread safe and fast (enough) for most
situations. However, there is an overhead whenever the deque -- a list-like
container -- needs to be transformed into a numpy array. Because
``DvG_RingBuffer`` already returns numpy arrays it will outperform a
``collections.deque()`` easily, tested to be a factor of ~60.

.. warning::

    * This ring buffer is not thread safe. You'll have to implement your own
      mutex locks when using this ring buffer in multithreaded operations.

    * The data array that is returned by a full ring buffer is a pass by
      reference of the *unwrap* buffer. It is not a copy! Hence, changing
      values in the returned data array is identical to changing values in the
      *unwrap* buffer.

Methods
-------
* ``clear()``
* ``append()``
* ``appendleft()``
* ``extend()``
* ``extendleft()``
* ``pop()``
* ``popleft()``

Properties
----------
* ``is_full``
* ``unwrap_address``
* ``current_address``
* ``dtype``
* ``shape``
* ``maxlen``

Indexing & slicing
------------------
* ``[]`` including negative indices and slicing
