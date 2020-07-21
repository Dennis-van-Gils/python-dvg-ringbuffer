import unittest
import numpy as np
from dvg_ringbuffer import RingBuffer


class TestAll(unittest.TestCase):
    def test_dtype(self):
        r = RingBuffer(5)
        self.assertEqual(r.dtype, np.dtype(np.float64))

        r = RingBuffer(5, dtype=np.bool)
        self.assertEqual(r.dtype, np.dtype(np.bool))

    def test_sizes(self):
        r = RingBuffer(5, dtype=(int, 2))
        self.assertEqual(r.maxlen, 5)
        self.assertEqual(len(r), 0)
        self.assertEqual(r.shape, (0, 2))

        r.append([0, 0])
        self.assertEqual(r.maxlen, 5)
        self.assertEqual(len(r), 1)
        self.assertEqual(r.shape, (1, 2))

    def test_append(self):
        r = RingBuffer(5)

        r.append(1)
        np.testing.assert_equal(r, np.array([1]))
        self.assertEqual(len(r), 1)

        r.append(2)
        np.testing.assert_equal(r, np.array([1, 2]))
        self.assertEqual(len(r), 2)

        r.append(3)
        r.append(4)
        r.append(5)
        np.testing.assert_equal(r, np.array([1, 2, 3, 4, 5]))
        self.assertEqual(len(r), 5)

        r.append(6)
        np.testing.assert_equal(r, np.array([2, 3, 4, 5, 6]))
        self.assertEqual(len(r), 5)

        self.assertEqual(r[4], 6)
        self.assertEqual(r[-1], 6)

    def test_getitem(self):
        r = RingBuffer(5)

        r.extend([1, 2, 3, 4, 5, 6])
        expected = np.array([2, 3, 4, 5, 6])
        np.testing.assert_equal(r, expected)

        for i in range(r.maxlen):
            self.assertEqual(expected[i], r[i])

        ii = [0, 4, 3, 1, 2]
        np.testing.assert_equal(r[ii], expected[ii])

    def test_extend(self):
        r = RingBuffer(5)

        r.extend([1, 2, 3])
        np.testing.assert_equal(r, np.array([1, 2, 3]))

        r.extend([4, 5, 6])
        np.testing.assert_equal(r, np.array([2, 3, 4, 5, 6]))

        r.extend([1, 2, 3, 4, 5, 6, 7])
        np.testing.assert_equal(r, np.array([3, 4, 5, 6, 7]))

    def test_2d(self):
        r = RingBuffer(3, dtype=(np.float, 2))

        r.append([1, 2])
        np.testing.assert_equal(r, np.array([[1, 2]]))
        self.assertEqual(len(r), 1)
        self.assertEqual(np.shape(r), (1, 2))

        r.append([3, 4])
        np.testing.assert_equal(r, np.array([[1, 2], [3, 4]]))
        self.assertEqual(len(r), 2)
        self.assertEqual(np.shape(r), (2, 2))

        r.append([5, 6])
        np.testing.assert_equal(r, np.array([[1, 2], [3, 4], [5, 6]]))
        self.assertEqual(len(r), 3)
        self.assertEqual(np.shape(r), (3, 2))

        r.append([7, 8])
        np.testing.assert_equal(r, np.array([[3, 4], [5, 6], [7, 8]]))
        self.assertEqual(len(r), 3)
        self.assertEqual(np.shape(r), (3, 2))

        np.testing.assert_equal(r[0], [3, 4])
        np.testing.assert_equal(r[0, :], [3, 4])
        np.testing.assert_equal(r[:, 0], [3, 5, 7])

    def test_iter(self):
        r = RingBuffer(5)
        for i in range(5):
            r.append(i)
        for i, j in zip(r, range(5)):
            self.assertEqual(i, j)

    def test_repr(self):
        r = RingBuffer(5, dtype=np.int)
        for i in range(5):
            r.append(i)

        self.assertEqual(repr(r), "<RingBuffer of array([0, 1, 2, 3, 4])>")

    def test_no_overwrite(self):
        r = RingBuffer(3, allow_overwrite=False)
        r.append(1)
        r.append(2)
        r.append(3)
        with self.assertRaisesRegex(IndexError, "overwrite"):
            r.append(4)
        with self.assertRaisesRegex(IndexError, "overwrite"):
            r.extend([4])
        r.extend([])

    def test_degenerate(self):
        r = RingBuffer(0)
        np.testing.assert_equal(r, np.array([]))

        # this does not error with deque(maxlen=0), so should not error here
        try:
            r.append(0)
        except IndexError:
            self.fail()


if not hasattr(TestAll, "assertRaisesRegex"):
    TestAll.assertRaisesRegex = TestAll.assertRaisesRegexp

if __name__ == "__main__":
    unittest.main()
