from pykakasi import kakasi
import numpy as np
import csv
import os.path

class FilesManager:
    '''
    loads and writes to files (such as CSV and parameters)
    '''
    def __init__(self):
        pass

    def load_dataset(self, botname="okan"):
        '''
        loads the csv file with datasets (named dataset_<botname>.csv, inside /csv directory)
        ignores the first row.
        ignores rows whose second columns are empty (i.e. unlabeled)
        return as list where each line is a pair of a string and integer, like
        [["Input sentense desu~~", 3], ["next input desu!", 1]]
        '''
        path = os.path.abspath("csv/dataset_"+botname+".csv")
        dataset_raw = self.__load_csv(path)
        dataset = []
        # ignore the first line (it's a header row)
        for line in dataset_raw[1:]:
            if self.__check_int(line[1]):
                # the second column is an integer
                dataset.append([line[0], int(line[1])])
            # otherwise, consider that line is not filled out properly and ignore.
        return dataset

    def __check_int(self, string):
        '''
        checks if a given string is an integer.
        https://stackoverflow.com/questions/1265665/how-can-i-check-if-a-string-represents-an-int-without-using-try-except
        '''
        try:
            int(string)
            return True
        except ValueError:
            return False
        
    def load_phrases(self, botname="okan"):
        '''
        loads the csv file with phrases for the chatbot (named phrases_<botname>.csv, inside /csv directory)
        the first row is ignored, as are rows whose first columns do not contain integers.
        Returns as a dictionary.
        the key is the integer index, and the value is a list of all the phrases in it.
        '''
        path = os.path.abspath("csv/phrases_"+botname+".csv")
        phrases_raw = self.__load_csv(path)
        phrases = {}
        # ignore the first line
        for line in phrases_raw[1:]:
            if self.__check_int(line[0]):
                dict = []
                for item in line[1:]:
                    if item != "":
                        # if the element actually contains a phrase
                        dict.append(item)
                phrases[int(line[0])] = dict
        return phrases
        
    def __load_csv(self, path):
        '''
        loads csv file, and returns it as a list
        '''
        print("opening file ", path)
        list_to_return = []
        with open(path) as csvfile:
            reader = csv.reader(csvfile)
            for line in reader:
                list_to_return.append(line)
        return list_to_return
            
class Parser:
    '''
    reads in a sentence in Japanese and outputs it as a vector.
    uses the pykakasi library to convert Japanese text into hiragana, then change
    that into a series of one-hot vectors for inputting into an RNN.
    https://github.com/miurahr/pykakasi
    https://qiita.com/almichest/items/52f871ee22e4a44346d4
    '''
    def __init__(self, debug=True):
        self.kakasi = kakasi()
        self.kakasi.setMode("H", "H")
        self.kakasi.setMode("K", "H")
        self.kakasi.setMode("J", "H")
        self.conv = self.kakasi.getConverter()
        self.dictionary = self.__getDictionary()
        self.debug = debug

    def sentence2vecs(self, input):
        '''
        input a sentence in Japanese, it turns it into Hiragana then makes it
        into a 50-ish dimensional vector
        '''
        hiragana = self.conv.do(input)
        if self.debug:
            print("入力文：" + input)
            print("ひらがな化された文：" + hiragana)
        data = []
        ignored = ""
        for char in hiragana:
            try:
                data.append(self.__character2number(char))
            except TypeError:
                ignored += char
        if self.debug:
            print("番号化された文：" + str(data))
            print("無視された文字：" + str(ignored))
        vecs = np.zeros((len(data), len(self.dictionary)))
        for i in range(len(data)):
            vecs[i][data[i]] = 1
        if self.debug:
            print("ベクトル化された文章：" + str(vecs))
            print("形：" + str(vecs.shape))
        return vecs

    def __character2number(self, char):
        for i in range(len(self.dictionary)):
            for item in self.dictionary[i]:
                if char == item:
                    return i
        raise TypeError

    def __getDictionary(self):
        return [['あ'], ['い'], ['う'], ['え'], ['お'],
                ['か'], ['き'], ['く'], ['け'], ['こ'],
                ['さ'], ['し'], ['す'], ['せ'], ['そ'],
                ['た'], ['ち'], ['つ'], ['て'], ['と'],
                ['な'], ['に'], ['ぬ'], ['ね'], ['の'],
                ['は'], ['ひ'], ['ふ'], ['へ'], ['ほ'],
                ['ま'], ['み'], ['む'], ['め'], ['も'],
                ['や'], ['ゆ'], ['よ'],
                ['ら'], ['り'], ['る'], ['れ'], ['ろ'],
                ['わ'], ['を'], ['ん'], ['？']]


if __name__ == "__main__":
    parser = Parser()
    parser.sentence2vecs("今日は、いい天気なのかな？笑 m(_ _)m")
    fm = FilesManager()
    print(fm.load_dataset())
    print(fm.load_phrases())
