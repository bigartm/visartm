# -*- coding: utf-8 -*-
import os
import re
import numpy as np
from random import randint
import pymorphy2


class BowBuilder:
    def __init__(self, dataset_name, language="russian"):
        self.dataset_name = dataset_name
        self.dataset_folder = os.path.join(
            "D:\\visartm\\data\\datasets", dataset_name)
        self.documents_dir = os.path.join(self.dataset_folder, "documents")
        self.word_index_dir = os.path.join(self.dataset_folder, "word_index")
        self.uci_dir = os.path.join(self.dataset_folder, "UCI")
        self.language = language
        self.morph = pymorphy2.MorphAnalyzer()

        os.makedirs(self.word_index_dir, exist_ok=True)
        os.makedirs(self.uci_dir, exist_ok=True)
        self.docs = dict()
        self.terms_count = 0
        self.docs_count = 0
        self.words = dict()
        self.words_index = dict()
        self.term_occur_count = np.zeros(5000000)
        self.filtered_words_index = None
        self.word_index_dict = dict()

    def lemmatize(self, word):
        word = word.lower()
        if word[0] == "#":
            return word
        return self.morph.parse(word)[0].normal_form

    def get_word_id(self, word_text):
        word_text = self.lemmatize(word_text)
        if word_text in self.words:
            word_id = self.words[word_text]
        else:
            return -1

        if self.filtered_words_index is None:
            return word_id
        else:
            if word_id in self.filtered_words_index:
                return self.filtered_words_index[word_id]
            else:
                return -1

    def begin_new_doc(self, doc_id):
        if doc_id not in self.word_index_dict:
            self.word_index_dict[doc_id] = []
        self.current_word_index = self.word_index_dict[doc_id]
        self.docs_count = max(self.docs_count, doc_id)
        if doc_id not in self.docs:
            self.docs[doc_id] = dict()
        self.cur_doc = self.docs[doc_id]

    def add_word_text(self, word_text, init_pos, length):
        word_text = self.lemmatize(word_text)

        if word_text in self.words:
            word_id = self.words[word_text]
        else:
            self.terms_count += 1
            self.words[word_text] = self.terms_count
            self.words_index[self.terms_count] = word_text
            word_id = self.terms_count

        if word_id not in self.cur_doc:
            self.cur_doc[word_id] = 1
        else:
            self.cur_doc[word_id] += 1
        self.term_occur_count[word_id] += 1

        self.current_word_index.append((init_pos, length, word_id))

    def filter_words(self):
        self.filtered_words_index = dict()
        ctr = 0

        fn = os.path.join(self.uci_dir, "vocab." + self.dataset_name + ".txt")
        with open(fn, "w", encoding="utf-8") as f:
            for i in range(1, self.terms_count + 1):
                # if self.is_english(self.words_index[i]):
                #    continue
                word = self.words_index[i]
                count = self.term_occur_count[i]
                # print("word", word)
                if len(word) > 2 and count < self.docs_count and count > 3:
                    ctr += 1
                    self.filtered_words_index[i] = ctr
                    if word[0] == '#':
                        f.write(word + " hashtag\n")
                    else:
                        f.write(word + " word\n")
        self.terms_count = ctr

    def is_english(self, word):
        for c in word:
            if c >= 'a' and c <= 'z':
                return True
        return False

    def char_good(self, c):
        return (c.isalpha() or c in '#_')

    # TODO: Make generator
    def parse_text(self, doc_file_name):
        with open(doc_file_name, 'r', encoding='utf-8') as f:
            line = f.read()

        cur_pos = 0
        bracket_level = 0
        line_len = len(line)
        while cur_pos < line_len:
            while cur_pos < line_len and not self.char_good(line[cur_pos]):
                c = line[cur_pos]
                if (c == '{' or c == '['):
                    bracket_level += 1
                if (c == '}' or c == ']'):
                    bracket_level -= 1
                cur_pos += 1
            init_pos = cur_pos

            while cur_pos < line_len and self.char_good(line[cur_pos]):
                cur_pos += 1

            length = cur_pos - init_pos
            word = line[init_pos: init_pos + length]
            if len(word) > 1:
                self.add_word_text(word, init_pos, length)

    def process(self):
        print("Reading documents")
        jj = 0
        for file_name in os.listdir(self.documents_dir):
            doc_file_name = os.path.join(self.documents_dir, file_name)
            id = int(file_name.split('.')[0])
            self.begin_new_doc(id)
            self.parse_text(doc_file_name)
            jj += 1
            if jj % 100 == 0:
                print(jj)

        print("Filtering words")
        self.filter_words()

        print("Writing index")
        jj = 0
        for doc_id, word_index in self.word_index_dict.items():
            fn = os.path.join(self.word_index_dir, str(doc_id) + ".txt")
            with open(fn, "w") as f:
                for entry in word_index:
                    word_id = entry[2]
                    if word_id in self.filtered_words_index:
                        f.write("%d %d %d\n" %
                                (entry[0], entry[1],
                                 self.filtered_words_index[word_id]))
            jj += 1
            if jj % 100 == 0:
                print(jj)

        print("Writing UCI docword")
        entries = []
        for doc_id, doc in self.docs.items():
            empty = True
            for word_id, count in doc.items():
                if word_id in self.filtered_words_index:
                    word_id_f = str(self.filtered_words_index[word_id])
                    entries.append(
                        str(doc_id) + " " + word_id_f + " " + str(count))
                    empty = False
            if empty:
                entries.append(str(doc_id) + " " +
                               str(randint(0, 1000)) + " 1")
                print("Warning! Empty document! (" + str(doc_id) + ")")

        fn = os.path.join(self.uci_dir, ("docword.%s.txt" % self.dataset_name))
        with open(fn, "w") as f:
            f.write(str(self.docs_count) + "\n")
            f.write(str(self.terms_count) + "\n")
            f.write(str(len(entries)) + "\n")
            for entry in entries:
                f.write(entry + "\n")


if __name__ == "__main__":
    builder = BowBuilder("lurkopub3000")
    builder.process()
