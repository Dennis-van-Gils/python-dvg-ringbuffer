.. image:: https://img.shields.io/pypi/v/dvg-ringbuffer
    :target: https://pypi.org/project/dvg-ringbuffer
.. image:: https://img.shields.io/pypi/pyversions/dvg-ringbuffer
    :target: https://pypi.org/project/dvg-ringbuffer
.. image:: https://travis-ci.com/Dennis-van-Gils/python-dvg-ringbuffer.svg?branch=master
    :target: https://travis-ci.com/Dennis-van-Gils/python-dvg-ringbuffer
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
*Provides a numpy ring buffer at a fixed memory address to allow for
significantly sped up* ``numpy``, ``sigpy``, ``numba`` *&* ``pyFFTW``
*calculations.*

- Github: https://github.com/Dennis-van-Gils/python-dvg-ringbuffer
- PyPI: https://pypi.org/project/dvg-ringbuffer

Installation::

    pip install dvg-ringbuffer

Based on:

    https://pypi.org/project/numpy_ringbuffer/ by Eric Wieser.

    ``DvG_RingBuffer`` can be used as a drop-in replacement for
    ``numpy_ringbuffer`` and provides several optimizations and extra features,
    but requires Python 3.

If and only if the ring buffer is completely full, will it return its array
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

API
===

``class RingBuffer(capacity, dtype=np.float64, allow_overwrite=True)``
----------------------------------------------------------------------
    Create a new ring buffer with the given capacity and element type.

        Args:
            capacity (``int``):
                The maximum capacity of the ring buffer

            dtype (``data-type``, optional):
                Desired type of buffer elements. Use a type like ``(float, 2)``
                to produce a buffer with shape ``(capacity, 2)``.

                Default: ``np.float64``

            allow_overwrite (``bool``, optional):
                If ``False``, throw an IndexError when trying to append to an
                already full buffer.

                Default: ``True``

Methods
-------
* ``clear()``
* ``append(value)``
    Append a single value to the ring buffer.

    .. code-block:: python

        rb = RingBuffer(3, dtype=np.int)  #  []
        rb.append(1)                      #  [1]
        rb.append(2)                      #  [1, 2]
        rb.append(3)                      #  [1, 2, 3]
        rb.append(4)                      #  [2, 3, 4]

* ``appendleft(value)``
    Append a single value to the ring buffer from the left side.

    .. code-block:: python

        rb = RingBuffer(3, dtype=np.int)  #  []
        rb.appendleft(1)                  #  [1]
        rb.appendleft(2)                  #  [2, 1]
        rb.appendleft(3)                  #  [3, 2, 1]
        rb.appendleft(4)                  #  [4, 3, 2]

* ``extend(values)``
    Extend the ring buffer with a list of values.

    .. code-block:: python

        rb = RingBuffer(3, dtype=np.int)  #  []
        rb.extend([1])                    #  [1]
        rb.extend([2, 3])                 #  [1, 2, 3]
        rb.extend([4, 5, 6, 7])           #  [5, 6, 7]

* ``extendleft(values)``
    Extend the ring buffer with a list of values from the left side.

    .. code-block:: python

        rb = RingBuffer(3, dtype=np.int)  #  []
        rb.extendleft([1])                #  [1]
        rb.extendleft([3, 2])             #  [3, 2, 1]
        rb.extendleft([7, 6, 5, 4])       #  [7, 6, 5]

* ``pop()``
    Remove the right-most item from the ring buffer and return it.

* ``popleft()``
    Remove the left-most item from the ring buffer and return it.

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

    .. code-block:: python

        from dvg_ringbuffer import RingBuffer

        rb = RingBuffer(4, dtype=np.int)  # --> rb[:] = array([], dtype=int32)
        rb.extend([1, 2, 3, 4, 5])        # --> rb[:] = array([2, 3, 4, 5])
        x = rb[0]                         # --> x = 2
        x = rb[-1]                        # --> x = 5
        x = rb[:3]                        # --> x = array([2, 3, 4])
        x = rb[np.array([0, 2, -1])]      # --> x = array([2, 4, 5])

        rb = RingBuffer(5, dtype=(np.int, 2))  # --> rb[:] = array([], shape=(0, 2), dtype=int32)
        rb.append([1, 2])                      # --> rb[:] = array([[1, 2]])
        rb.append([3, 4])                      # --> rb[:] = array([[1, 2], [3, 4]])
        rb.append([5, 6])                      # --> rb[:] = array([[1, 2], [3, 4], [5, 6]])
        x = rb[0]                              # --> x = array([1, 2])
        x = rb[0, :]                           # --> x = array([1, 2])
        x = rb[:, 0]                           # --> x = array([1, 3, 5])
