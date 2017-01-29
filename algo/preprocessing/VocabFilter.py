# -*- coding: utf-8 -*-
import os 
import re
import numpy as np
from random import randint
import pymorphy2
            
            
class VocabFilter():
    def __init__(self, vw_file):
        self.lower_bound = 0
        self.upper_bound = 1000000
        self.upper_bound_relative = 1000000
        self.documents_count = 0
        self.total_terms_count = 0
        
        self.vocab = dict()
        with open(vw_file, "r", encoding = "utf-8") as f:
            for line in f:
                self.documents_count += 1
                current_modality = '@default_class'
                parsed_vw = line.split()
                for term in parsed_vw[1:]:
                    if term[0] == '|':
                        current_modality = term[1:]
                    else:
                        parsed_term = term.split(':')
                        key = parsed_term[0] + " " + current_modality
                        if ':' in term:
                            count = int(parsed_term[1])
                        else:
                            count = 1
                        try:
                            self.vocab[key] += count
                        except:
                            self.vocab[key] = count
                        self.total_terms_count += count
    
    def save_vocabulary(self, vocab_file):
        with open(vocab_file, "w", encoding = "utf-8") as f:
            for word, count in self.vocab.items():
                upper_bound = min(self.upper_bound, self.upper_bound_relative*self.documents_count)
                if count >= self.lower_bound and count <= upper_bound:
                    f.write(word + "\n")
        

if __name__ == "__main__":
    filter = VocabFilter("D:\\visartm\\data\\datasets\\postnauka\\vw.txt")
    print("initilized")
    filter.lower_bound = 5
    filter.upper_bound_relative = 2
    filter.save_vocabulary("D:\\visartm\\data\\datasets\\postnauka\\vocab.txt")
    

