# -*- coding: utf-8 -*-
import os
import pymorphy2


class Parser:
    def __init__(self, dataset_folder):
        self.documents_folder = os.path.join(dataset_folder, "documents")
        self.output_folder = os.path.join(dataset_folder, "wordpos")
        os.makedirs(self.output_folder, exist_ok=True)
        self.morph = pymorphy2.MorphAnalyzer()
        self.vw_file = open(
            os.path.join(
                dataset_folder,
                "vw.txt"),
            "w",
            encoding="utf-8")
        self.lemmatized = dict()

        self.store_order = False
        self.hashtags = False
        self.bigrams = False

        self.ctr = 0

        self.meta_vw = dict()
        meta_vw_file = os.path.join(dataset_folder, "meta", "meta.vw.txt")
        if os.path.exists(meta_vw_file):
            with open(meta_vw_file, "r", encoding='utf-8') as f:
                for line in f:
                    pos = line.find(' ')
                    self.meta_vw[line[0:pos]] = line[pos:-1]

        self.char_good = lambda c: c.isalpha()

    def lemmatize(self, word):
        word = word.lower()
        try:
            return self.lemmatized[word]
        except BaseException:
            if word[0] == "#":
                ans = word
            else:
                ans = self.morph.parse(word)[0].normal_form
            self.lemmatized[word] = ans
            return ans

    def process_document(self, rel_name, doc_name):
        file_name = os.path.join(self.documents_folder, rel_name)
        with open(file_name, "r", encoding='utf-8') as f:
            text = f.read()

        self.vw_file.write(rel_name + " |word")
        bow = dict()
        hashtags = []
        bigrams = dict()

        wordpos_file = open(
            os.path.join(
                self.output_folder,
                rel_name),
            "w",
            encoding='utf-8')

        cur_pos = 0
        prev_word = None
        prev_word_start_pos = 0
        text_len = len(text)
        while cur_pos < text_len:
            while cur_pos < text_len and not self.char_good(text[cur_pos]):
                if text[cur_pos] in "\n.!?":
                    prev_word = None
                cur_pos += 1
            init_pos = cur_pos

            while cur_pos < text_len and self.char_good(text[cur_pos]):
                cur_pos += 1

            length = cur_pos - init_pos
            word = text[init_pos: cur_pos]
            if length > 1:
                word_lemmatized = self.lemmatize(word)
                if len(word_lemmatized) <= 1:
                    continue

                if word_lemmatized[0] == '#' and self.hashtags:
                    wordpos_file.write(
                        "%d %d %s$#hashtag\n" %
                        (init_pos, length, word_lemmatized))
                    hashtags.append(word_lemmatized)
                    prev_word = None
                else:
                    if self.bigrams:
                        if prev_word:
                            bigram_text = prev_word + "_" + word_lemmatized
                            bigram_pos = prev_word_start_pos
                            bigram_length = init_pos + \
                                length - prev_word_start_pos
                            wordpos_file.write(
                                "%d %d %s$#bigram\n" %
                                (bigram_pos, bigram_length, bigram_text))
                            try:
                                bigrams[bigram_text] += 1
                            except BaseException:
                                bigrams[bigram_text] = 1
                        prev_word_start_pos = init_pos
                        prev_word = word_lemmatized
                    wordpos_file.write(
                        "%d %d %s$#word\n" %
                        (init_pos, length, word_lemmatized))
                    if self.store_order:
                        self.vw_file.write(" " + word_lemmatized)
                    else:
                        if word_lemmatized in bow:
                            bow[word_lemmatized] += 1
                        else:
                            bow[word_lemmatized] = 1

        if not self.store_order:
            for word, count in bow.items():
                if count == 1:
                    self.vw_file.write(" %s" % word)
                else:
                    self.vw_file.write(" %s:%d" % (word, count))

        if len(hashtags) > 0:
            self.vw_file.write(" |hashtag " + ' '.join(hashtags))

        if len(bigrams) > 0:
            self.vw_file.write(" |bigram")
            for word, count in bigrams.items():
                if count == 1:
                    self.vw_file.write(" %s" % word)
                else:
                    self.vw_file.write(" %s:%d" % (word, count))

        if rel_name in self.meta_vw:
            self.vw_file.write(self.meta_vw[rel_name])
        elif doc_name in self.meta_vw:
            self.vw_file.write(self.meta_vw[doc_name])
        self.vw_file.write("\n")
        wordpos_file.close()

        self.ctr += 1
        # if self.ctr % 100 == 0:
        #    print(self.ctr)

    def process(self):
        if self.hashtags:
            self.char_good = lambda c: c.isalpha() or c in '#_'

        root_path_length = len(self.documents_folder)
        for root, subdirs, files in os.walk(self.documents_folder):
            rel_foler_path = root[root_path_length + 1:]
            for subdir in subdirs:
                rel_subdir = os.path.join(rel_foler_path, subdir)
                os.makedirs(
                    os.path.join(
                        self.output_folder,
                        rel_subdir),
                    exist_ok=True)
            for file in files:
                rel_file_name = os.path.join(rel_foler_path, file)
                self.process_document(rel_file_name, file)
        self.vw_file.close()


if __name__ == "__main__":
    parser = Parser("D:\\visartm\\data\\datasets\\lurkopub1000")
    parser.hashtags = True
    parser.bigrams = True
    parser.store_order = False

    parser.process()
