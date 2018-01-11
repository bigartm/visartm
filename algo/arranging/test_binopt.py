import unittest
import numpy as np

import algo.arranging.binopt as binopt


class TestBinopt(unittest.TestCase):
    def setUp(self):
        pass

    def test_binopt_trivial(self):
        # x1 -> min, unconditional.
        # Answer is [0]
        A = np.array([[]])
        b = np.array([])
        c = np.array([1])
        ans = binopt.minimize_binary_lp(A, b, c)
        np.testing.assert_array_equal(ans, [0])

        # x1+x2+x3  -> max, unconditional.
        # Answer is [1, 1, 1]
        A = np.array([[]])
        b = np.array([])
        c = np.array([-1, -1, -1])
        ans = binopt.minimize_binary_lp(A, b, c)
        np.testing.assert_array_equal(ans, [1, 1, 1])

        # x1+x2+x3 -> min, unconditional.
        # s.t. x1+x2+x3 >= 3
        # Answer is [1,1]
        A = np.array([[-1, -1, -1]])
        b = np.array([-3])
        c = np.array([1, 1, 1])
        ans = binopt.minimize_binary_lp(A, b, c)
        np.testing.assert_array_equal(ans, [1, 1, 1])

        # x_1 + x_2 + x_3 -> min
        # s.t. - x_1 - x_2 <= -1
        #      - x_2 - x_3 <= -1
        # Answer is [0, 1, 0]
        A = np.array([[-1, -1, 0], [0, -1, -1]])
        b = np.array([-1, -1])
        c = np.array([1, 1, 1])
        ans = binopt.minimize_binary_lp(A, b, c)
        np.testing.assert_array_equal(ans, [0, 1, 0])

        # x_1 -> min
        # s.t. x1 >= 2
        # Impossible.
        A = np.array([[-1]])
        b = np.array([-2])
        c = np.array([1])
        ans = binopt.minimize_binary_lp(A, b, c)
        self.assertIsNone(ans)

    def test_non_trivial(self):
        # x1+x2+x3+x4+x5+x6+x7 ->min
        # st: x2+2*x3+2*x4+x5+x6+x7>=1
        #     2*x2+2*x3+x4+2*x6>=2
        #     x3+2*x4+2*x5+x7>=1
        #     x2+x3+2*x4+x5+2*x7>=2
        A = np.array([[0, -1, -2, -2, -1, -1, -1],
                      [0, -2, -2, -1, 0, -2, 0],
                      [0, 0, -1, -2, -2, 0, -1],
                      [0, -1, -1, -2, -1, 0, -2]])
        b = np.array([-1, -2, -1, -2])
        c = np.array([1, 1, 1, 1, 1, 1, 1])
        ans = binopt.minimize_binary_lp(A, b, c)
        np.testing.assert_array_equal(ans, [0, 1, 0, 1, 0, 0, 0])

    def test_binopt_sparse(self):
        # x0 + x1 + .... + x99 ->min
        # x11+x22 >= 1
        # x22+x33+x44 >= 2
        # x44+x55 >= 1
        # Answer: x22=x44=1, rest are zeros.
        A = [{11: -1, 22: -1}, {22: -1, 33: -1, 44: -1}, {44: -1, 55: -1}]
        b = np.array([-1, -2, -1])
        c = np.array([1 for i in range(100)])
        ans = binopt.minimize_binary_lp(A, b, c)
        correct = [0 for i in range(100)]
        correct[22] = 1
        correct[44] = 1
        np.testing.assert_array_equal(ans, correct)
