from pykakasi import kakasi
import numpy as np
'''
uses the pykakasi library to convert Japanese text into hiragana, then change
that into a series of one-hot vectors for inputting into an RNN.
https://github.com/miurahr/pykakasi
https://qiita.com/almichest/items/52f871ee22e4a44346d4
'''


class Parser:
    '''
    reads in a sentence in Japanese and outputs it as a vector.
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
