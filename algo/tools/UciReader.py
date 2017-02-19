class UciReader:
    def __init__(self, docword_file, vocab_file):
        self.vocab = dict()
        with open(vocab_file, "r", encoding = "utf-8") as f:
            i = 1
            for line in f:
                parsed = line.split()
                if len(parsed) == 2:
                    self.vocab[i] = line.split()
                else:
                    self.vocab[i] = (line, "@default_class")
                i+=1
    
    def write_doc(self):
        self.out.write("%s.txt " % (str(self.cur_doc_id)))
        for modality, string in self.bow.items():
            self.out.write("|%s %s" % (modality, string))
        self.out.write("\n")
        if self.cur_doc_id % 100 == 0:
            print(self.cur_doc_id)
        self.bow = {}
                
    def save_vw(self, output_file):
        self.out = open(output_file, "w", encoding = 'utf-8')
        self.cur_doc_id = 1
        self.bow = dict()
        with open(docword_file, "r", encoding = "utf-8") as f:
            for line in f:
                parsed = line.split()
                if len(parsed) != 3:
                    continue
                doc_id = int(parsed[0])
                if doc_id != self.cur_doc_id:
                    self.write_doc()
                    self.cur_doc_id = doc_id
                word, modality = self.vocab[int(parsed[1])]
                count = parsed[2]
                write = word
                if ':' in word:
                    print("Warning! Colon found! Term ignored.")
                    continue
                if count != "1":
                    write += ':' + count
                try:
                    self.bow[modality] += write + ' '
                except:
                    self.bow[modality] = write + ' '
                #if self.cur_doc_id == 100:
                #    break
        self.write_doc()
        self.out.close()




if __name__ == "__main__":
    docword_file = "D:\\visartm\\data\\datasets\\lenta\\UCI\\docword.lenta.txt"
    vocab_file = "D:\\visartm\\data\\datasets\\lenta\\UCI\\vocab.lenta.txt"
    output_file = "D:\\visartm\\data\\datasets\\lenta\\vw.txt"
    uci = UciReader(docword_file, vocab_file)
    uci.save_vw(output_file)
