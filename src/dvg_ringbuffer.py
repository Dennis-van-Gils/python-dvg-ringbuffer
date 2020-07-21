#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numpy ringbuffer at a **fixed** memory address to allow for significantly
sped up *numpy*, *sigpy*, *numba* & *pyFFTW*  calculations.

If, and only if the ring buffer is completely full, will it return its array
data as a contiguous C-style numpy array at a single fixed memory address per
ring buffer instance. It does so by unwrapping the discontiguous ring buffer
array into a second extra *unwrap* buffer that is a private member of the ring
buffer class. This is advantegeous for other accelerated computations by, e.g.,
*numpy*, *sigpy*, *numba*, *pyFFTW*, that benefit from being fed with
contiguous arrays at the same memory address each time again, such that compiler
optimizations and data planning are made possible.

When the ring buffer is not completely full, it will return its data as a
contiguous C-style numpy array, but at different memory addresses.

Commonly, ``collections.deque()`` is used to act as a ring buffer. The
benefits of a deque is that it is thread safe and fast (enough) for most
situations. However, there is an overhead whenever the deque (a list-like
container) needs to be transformed into a numpy array. Class
``DvG_RingBuffer()`` will outperform a ``collections.deque()`` easily
(tested to be a factor of ~39).

.. warning::

    * This ring buffer is not thread safe. You have to implement your own
      mutex locks when using this ring buffer class in multi-threaded routines.

    * The data array that is returned by a full ring buffer is a pass by
      reference of the *unwrap* buffer. It is not a copy! Hence, changing
      values in the returned data array is identical to changing values in the
      *unwrap* buffer.

Based on
--------
https://pypi.org/project/numpy_ringbuffer/ by Eric Wieser.

DvG_RingBuffer can be used as a drop-in replacement for numpy_ringbuffer.

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

"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/python-dvg-ringbuffer"
__date__ = "21-07-2020"
__version__ = "1.0.0"

from collections.abc import Sequence
import numpy as np


class RingBuffer(Sequence):
    def __init__(self, capacity, dtype=np.float64, allow_overwrite=True):
        """Create a new ring buffer with the given capacity and element type.

        Args:
            capacity (int):
                The maximum capacity of the ring buffer

            dtype (data-type, optional):
                Desired type of buffer elements. Use a type like (float, 2) to
                produce a buffer with shape (N, 2).

                Default: np.float64

            allow_overwrite (bool, optional):
                If False, throw an IndexError when trying to append to an
                already full buffer.

                Default: True
        """
        if dtype == np.float64:
            p = {"shape": capacity, "fill_value": np.nan, "order": "C"}
            self._arr = np.full(**p)
            self._unwrap_buffer = np.full(**p)  # @ fixed memory address
        else:
            p = {"shape": capacity, "dtype": dtype, "order": "C"}
            self._arr = np.zeros(**p)
            self._unwrap_buffer = np.zeros(**p)  # @ fixed memory address

        self._N = capacity
        self._allow_overwrite = allow_overwrite
        self._idx_L = 0  # left index
        self._idx_R = 0  # right index
        self._unwrap_buffer_is_dirty = False

    # --------------------------------------------------------------------------
    #   clear
    # --------------------------------------------------------------------------

    def clear(self):
        self._idx_L = 0
        self._idx_R = 0

        if self._arr.dtype == np.float64:
            self._arr.fill(np.nan)
            self._unwrap_buffer.fill(np.nan)
        else:
            self._arr.fill(0)
            self._unwrap_buffer.fill(0)

    # --------------------------------------------------------------------------
    #   append
    # --------------------------------------------------------------------------

    def append(self, value):
        """Append a single value to the ring buffer.

        rb = RingBuffer(3, dtype=np.int)  # --> rb = []
        rb.append(1)                      # --> rb = [1]
        rb.append(2)                      # --> rb = [1, 2]
        rb.append(3)                      # --> rb = [1, 2, 3]
        rb.append(4)                      # --> rb = [2, 3, 4]
        """
        if self.is_full:
            if not self._allow_overwrite:
                raise IndexError(
                    "Append to a full RingBuffer with overwrite disabled."
                )
            self._idx_L += 1

        self._unwrap_buffer_is_dirty = True
        self._arr[self._idx_R % self._N] = value
        self._idx_R += 1
        self._fix_indices()

    def appendleft(self, value):
        """Append a single value to the ring buffer from the left side.

        rb = RingBuffer(3, dtype=np.int)  # --> rb = []
        rb.appendleft(1)                  # --> rb = [1]
        rb.appendleft(2)                  # --> rb = [2, 1]
        rb.appendleft(3)                  # --> rb = [3, 2, 1]
        rb.appendleft(4)                  # --> rb = [4, 3, 2]
        """
        if self.is_full:
            if not self._allow_overwrite:
                raise IndexError(
                    "Append to a full RingBuffer with overwrite disabled."
                )
            self._idx_R -= 1

        self._unwrap_buffer_is_dirty = True
        self._idx_L -= 1
        self._fix_indices()
        self._arr[self._idx_L] = value

    # --------------------------------------------------------------------------
    #   extend
    # --------------------------------------------------------------------------

    def extend(self, values):
        """Extend the ring buffer with a list of values.

        rb = RingBuffer(3, dtype=np.int)  # --> rb = []
        rb.extend([1])                    # --> rb = [1]
        rb.extend([2, 3])                 # --> rb = [1, 2, 3]
        rb.extend([4, 5, 6, 7])           # --> rb = [5, 6, 7]
        """
        lv = len(values)
        if len(self) + lv > self._N:
            if not self._allow_overwrite:
                raise IndexError(
                    "RingBuffer overflows, because overwrite is disabled."
                )

        self._unwrap_buffer_is_dirty = True
        if lv >= self._N:
            self._arr[...] = values[-self._N :]
            self._idx_R = self._N
            self._idx_L = 0
            return

        ri = self._idx_R % self._N
        sl1 = np.s_[ri : min(ri + lv, self._N)]
        sl2 = np.s_[: max(ri + lv - self._N, 0)]
        # fmt: off
        self._arr[sl1] = values[: sl1.stop - sl1.start]  # pylint: disable=no-member
        self._arr[sl2] = values[sl1.stop - sl1.start :]  # pylint: disable=no-member
        # fmt: on
        self._idx_R += lv
        self._idx_L = max(self._idx_L, self._idx_R - self._N)
        self._fix_indices()

    def extendleft(self, values):
        """Extend the ring buffer with a list of values from the left side.

        rb = RingBuffer(3, dtype=np.int)  # --> rb = []
        rb.extendleft([1])                # --> rb = [1]
        rb.extendleft([3, 2])             # --> rb = [3, 2, 1]
        rb.extendleft([7, 6, 5, 4])       # --> rb = [7, 6, 5]
        """
        lv = len(values)
        if len(self) + lv > self._N:
            if not self._allow_overwrite:
                raise IndexError(
                    "RingBuffer overflows, because overwrite is disabled."
                )

        self._unwrap_buffer_is_dirty = True
        if lv >= self._N:
            self._arr[...] = values[: self._N]
            self._idx_R = self._N
            self._idx_L = 0
            return

        self._idx_L -= lv
        self._fix_indices()
        li = self._idx_L
        sl1 = np.s_[li : min(li + lv, self._N)]
        sl2 = np.s_[: max(li + lv - self._N, 0)]
        # fmt: off
        self._arr[sl1] = values[:sl1.stop - sl1.start]  # pylint: disable=no-member
        self._arr[sl2] = values[sl1.stop - sl1.start:]  # pylint: disable=no-member
        # fmt: on
        self._idx_R = min(self._idx_R, self._idx_L + self._N)

    # --------------------------------------------------------------------------
    #   pop
    # --------------------------------------------------------------------------

    def pop(self):
        if len(self) == 0:
            raise IndexError("Pop from an empty RingBuffer.")
        self._unwrap_buffer_is_dirty = True
        self._idx_R -= 1
        self._fix_indices()
        return self._arr[self._idx_R % self._N]

    def popleft(self):
        if len(self) == 0:
            raise IndexError("Pop from an empty RingBuffer.")
        self._unwrap_buffer_is_dirty = True
        res = self._arr[self._idx_L]
        self._idx_L += 1
        self._fix_indices()
        return res

    # --------------------------------------------------------------------------
    #   Properties
    # --------------------------------------------------------------------------

    @property
    def is_full(self):
        return len(self) == self._N

    @property
    def unwrap_address(self):
        """Get the fixed memory address of the internal unwrap buffer, used when
        the ring buffer is completely full.
        """
        return self._unwrap_buffer[:].__array_interface__["data"][0]

    @property
    def current_address(self):
        """Get the current memory address of the array behind the buffer.
        """
        return self[:].__array_interface__["data"][0]

    @property
    def dtype(self):
        return self._arr.dtype

    @property
    def shape(self):
        return (len(self),) + self._arr.shape[1:]

    @property
    def maxlen(self):
        return self._N

    # --------------------------------------------------------------------------
    #   _unwrap
    # --------------------------------------------------------------------------

    def _unwrap(self):
        """Copy the data from this buffer into unwrapped form.
        """
        return np.concatenate(
            (
                self._arr[self._idx_L : min(self._idx_R, self._N)],
                self._arr[: max(self._idx_R - self._N, 0)],
            )
        )

    # --------------------------------------------------------------------------
    #   _unwrap_into_buffer
    # --------------------------------------------------------------------------

    def _unwrap_into_buffer(self):
        """Copy the data from this buffer into unwrapped form to the unwrap
        buffer at a fixed memory address. Only call when the buffer is full.
        """
        if self._unwrap_buffer_is_dirty:
            # print("Unwrap buffer was dirty")
            np.concatenate(
                (
                    self._arr[self._idx_L : min(self._idx_R, self._N)],
                    self._arr[: max(self._idx_R - self._N, 0)],
                ),
                out=self._unwrap_buffer,
            )
            self._unwrap_buffer_is_dirty = False
        else:
            # print("Unwrap buffer was clean")
            pass

    # --------------------------------------------------------------------------
    #   _fix_indices
    # --------------------------------------------------------------------------

    def _fix_indices(self):
        """Enforce our invariant that 0 <= self._idx_L < self._N.
        """
        if self._idx_L >= self._N:
            self._idx_L -= self._N
            self._idx_R -= self._N
        elif self._idx_L < 0:
            self._idx_L += self._N
            self._idx_R += self._N

    # --------------------------------------------------------------------------
    #   Dunder methods
    # --------------------------------------------------------------------------

    def __array__(self):
        """Numpy compatibility
        """
        # print("__array__")
        if self.is_full:
            self._unwrap_into_buffer()
            return self._unwrap_buffer
        else:
            return self._unwrap()

    def __len__(self):
        return self._idx_R - self._idx_L

    def __getitem__(self, item):

        # --------------------------
        #   ringbuffer[slice]
        #   ringbuffer[tuple]
        #   ringbuffer[None]
        # --------------------------

        if isinstance(item, (slice, tuple)) or item is None:
            if self.is_full:
                print("  --> _unwrap_buffer[item]")
                self._unwrap_into_buffer()
                return self._unwrap_buffer[item]

            print("  --> _unwrap()[item]")
            return self._unwrap()[item]

        # ----------------------------------
        #   ringbuffer[int]
        #   ringbuffer[list of ints]
        #   ringbuffer[np.ndarray of ints]
        # ----------------------------------

        if hasattr(item, "__len__"):
            item_arr = np.asarray(item)
        else:
            item_arr = np.asarray([item])

        if not issubclass(item_arr.dtype.type, np.integer):
            raise TypeError("RingBuffer indices must be integers.")

        # Check for `List index out of range`
        if len(self) == 0:
            raise IndexError(
                "RingBuffer list index out of range. The RingBuffer has "
                "length 0."
            )

        if np.any(item_arr < -len(self)) or np.any(item_arr >= len(self)):
            idx_under = item_arr[np.where(item_arr < -len(self))]
            idx_over = item_arr[np.where(item_arr >= len(self))]
            idx_oor = np.sort(np.concatenate((idx_under, idx_over)))
            raise IndexError(
                "RingBuffer list %s %s out of range. The RingBuffer has "
                "length %s."
                % (
                    "index" if len(idx_oor) == 1 else "indices",
                    idx_oor,
                    len(self),
                )
            )

        # Retrieve elements
        if item_arr.size == 1:
            # Single element: We can speed up the code
            print("  --> single element")
            if item_arr < 0:
                item_arr = (self._idx_R + item_arr) % self._N
            else:
                item_arr = (item_arr + self._idx_L) % self._N
        else:
            # Multiple elements
            print("  --> multiple elements")
            neg = np.where(item_arr < 0)
            pos = np.where(item_arr >= 0)

            if len(neg) > 0:
                item_arr[neg] = (self._idx_R + item_arr[neg]) % self._N
            if len(pos) > 0:
                item_arr[pos] = (item_arr[pos] + self._idx_L) % self._N

        print("  --> _arr[item_arr]")
        return self._arr[item_arr]

    def __iter__(self):
        # print("__iter__")
        if self.is_full:
            self._unwrap_into_buffer()
            return iter(self._unwrap_buffer)
        else:
            return iter(self._unwrap())

    def __repr__(self):
        return "<RingBuffer of {!r}>".format(np.asarray(self))
