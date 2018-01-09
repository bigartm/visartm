from django.test import TestCase
import unittest

from .models import BagOfWords


class ModalityMock:
    def __init__(self, index_id):
        self.index_id = index_id


class TermMock:
    def __init__(self, modality):
        self.modality = modality


class TestBagOfWords(unittest.TestCase):
    terms_index = dict()

    def setUp(self):
        # Create 10 words. 5 with modality "0" and 5 with modaity "1".
        modality0 = ModalityMock(0)
        modality1 = ModalityMock(1)

        for i in range(0, 5):
            self.terms_index[i] = TermMock(modality0)
        for i in range(5, 10):
            self.terms_index[i] = TermMock(modality1)

    def test_create_to_bytes(self):
        bow = BagOfWords()
        self.assertEqual(bow.to_bytes(self.terms_index), b'')

        bow.add_term(9, 1)
        term9_bytes = b'\x09\x00\x00\x00\x01\x00\x01'
        self.assertEqual(bow.to_bytes(self.terms_index), term9_bytes)

        bow.add_term(9, 7)
        term9_bytes = b'\x09\x00\x00\x00\x08\x00\x01'
        self.assertEqual(bow.to_bytes(self.terms_index), term9_bytes)

        bow.add_term(2, 257)
        term2_bytes = b'\x02\x00\x00\x00\x01\x01\x00'
        self.assertEqual(bow.to_bytes(self.terms_index),
                         term2_bytes + term9_bytes + b'z')
