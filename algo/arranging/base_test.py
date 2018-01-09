import unittest
import numpy as np

import algo.arranging.base as base


class TestArrangeTopics(unittest.TestCase):
    def setUp(self):
        pass

    def test_arrange_topics_phi(self):
        """Test for arrange_topics_phi.

        Creates a set of 9 topics with obvious correct arrangement,
        then arranges them and checks arrangement.
        Repeats 3 times.

        Uses exact slow algorithm for testing.
        If you have LKH algorithm installed locally and want to test it, change
        "hamilton_exact" to "hamilton".
        """
        for test_num in range(3):
            # generate phi matrix
            W = 100     # Number of words
            T = 9       # Number of topics
            phi = np.zeros((W, T))
            path = list(np.random.permutation(T))

            for i in range(T - 1):
                phi[i][path[i]] = 0.5
                phi[i][path[i + 1]] = 0.5

            phi[W - 1][path[0]] = 0.5
            phi[W - 2][path[T - 1]] = 0.5

            # call target function
            answer = base.arrange_topics_phi(phi, mode="hamilton_exact")

            # Check if obtained path is equal to initial (or probably reversed)
            self.assertTrue(path == answer or path == list(reversed(answer)))
