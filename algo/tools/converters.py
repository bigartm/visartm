class UciReader:
	def __init__(self, docword_file, vocab_file):
		self.vocab = dict()
		with open(vocab_file, "r", encoding = "utf-8") as f:
			i = 1
			for line in f:
				line = line.replace('\n','')
				parsed = line.split()
				if len(parsed) == 2: 
					self.vocab[i] = parsed
				else:
					self.vocab[i] = (line, "@default_class")
				i+=1
		self.docword_file = docword_file
	
	def write_doc(self):
		self.out.write("%06d.txt " % self.cur_doc_id)
		for modality, string in self.bow.items():
			self.out.write("|%s %s" % (modality, string))
		self.out.write("\n")
		#if self.cur_doc_id % 100 == 0:
		#	print(self.cur_doc_id)
		self.bow = {}
				
	def save_vw(self, output_file):
		self.out = open(output_file, "w", encoding = 'utf-8')
		self.cur_doc_id = 1
		self.bow = dict()
		with open(self.docword_file, "r", encoding = "utf-8") as f:
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
				#	break
		self.write_doc()
		self.out.close()

def uci2vw(docword_file_name, vocab_file_name, vw_file_name):
	uci = UciReader(docword_file_name, vocab_file_name)
	uci.save_vw(vw_file_name)		
		
import os
def vw2uci(vw_file_name, docword_file_name, vocab_file_name):
	vocab = dict() 
	temp_docword_file_name = os.path.join(os.path.dirname(vw_file_name), "temp.txt")
	temp_docword_file = open(temp_docword_file_name, "w")
	vocab_file = open(vocab_file_name, "w", encoding = 'utf-8')
	
	docs_counter = 0
	terms_counter = 0
	entries_counter = 0
	
	
	for line in open(vw_file_name, encoding = 'utf-8'):
		docs_counter += 1
		tokens = line.split()
		current_modality = "@default_class"
		bow = dict()
		for token in tokens[1:]:
			if token[0] == '|':
				current_modality = token[1:]
			else:
				parsed = token.split(':')
				try:
					cnt = int(parsed[1])
				except:
					cnt = 1
					
				word = parsed[0] + " " + current_modality
				try:
					wid = vocab[word]
				except:
					vocab_file.write(word + "\n")
					terms_counter += 1
					vocab[word] = terms_counter 
					wid = terms_counter 
				
				try:
					bow[wid] += cnt
				except:
					bow[wid] = cnt
		
		for key, value in sorted(bow.items()):
			temp_docword_file.write("%d %d %d\n" % (docs_counter, key, value) )
			entries_counter += 1
			
	temp_docword_file.close()
	vocab_file.close()
			
	with open(docword_file_name, "w") as f:
		f.write("%d\n%d\n%d\n" % (docs_counter, terms_counter, entries_counter) )
		for line in open(temp_docword_file_name):
			f.write(line)
	 

if __name__ == "__main__":
	docword_file = "D:\\visartm\\data\\datasets\\lenta\\UCI\\docword.lenta.txt"
	vocab_file = "D:\\visartm\\data\\datasets\\lenta\\UCI\\vocab.lenta.txt"
	output_file = "D:\\visartm\\data\\datasets\\lenta\\vw.txt"
	uci = UciReader(docword_file, vocab_file)
	uci.save_vw(output_file)
