import unittest
import numpy as np

import api


class TestArrangeTopics(unittest.TestCase):
    def setUp(self):
        pass

    # Test for arrange_topics
    # Creates a set of 10 topics
    # with obvious correct arrangement,
    # then arranges them and checks arrangement
    def test_arrange_topics(self):
        for test_num in range(10):
            # generate phi matrix
            W = 100     # Number of words
            T = 20         # Number of topics
            phi = np.zeros((W, T))
            path = list(np.random.permutation(T))

            for i in range(T - 1):
                phi[i][path[i]] = 0.5
                phi[i][path[i + 1]] = 0.5

            phi[W - 1][path[0]] = 0.5
            phi[W - 2][path[T - 1]] = 0.5

            # call target function
            answer = list(api.arrange_topics(phi))

            # Check if obtained path is equal to initial (or probably reversed)
            self.assertTrue(path == answer or path == list(reversed(answer)))


unittest.main()
