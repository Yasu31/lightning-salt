'''
The Neural Network interface for the chatbot.
Use this to train the NN as well as to actually use it.
Based on training.py, which was based on rnn3.py, which was based on
https://gist.github.com/danijar/3f3b547ff68effb03e20c470af22c696
https://danijar.com/variable-sequence-lengths-in-tensorflow/
https://medium.com/@erikhallstrm/using-the-tensorflow-lstm-api-3-7-5f2b97ca6b73#.a6ai9917d
'''
from __future__ import print_function, division
from Parser import Parser, FilesManager
import numpy as np
import tensorflow as tf

botname = "okan"

class NeuralNetwork:
    def __init__(self, botname="okan"):
        self.botname = botname

    def train(self):
        x, y = self.generateData()
        num_epochs = 20
        max_input_length = x.shape[1]  # maximum num of chacacters in the training data messages
        input_dimensions = x.shape[2]  # how many types of characters there are
        input_data_num = x.shape[0]  # how many different training data
        backprop_length = max_input_length
        state_size = 100
        num_classes = y.shape[1]  # how many types of output classes? (how many responses?)
        batch_size = 5


        batchX_placeholder = tf.placeholder(
            tf.float32, [None, backprop_length, input_dimensions])
        batchY_placeholder = tf.placeholder(tf.float32, [None, num_classes])
        cell_state = tf.placeholder(tf.float32, [None, state_size])
        hidden_state = tf.placeholder(tf.float32, [None, state_size])
        init_state = tf.contrib.rnn.LSTMStateTuple(cell_state, hidden_state)
        length_input = self.length(batchX_placeholder)
        output, current_state = tf.nn.dynamic_rnn(tf.contrib.rnn.BasicLSTMCell(state_size, state_is_tuple=True), batchX_placeholder, dtype=tf.float32, sequence_length=length_input)
        last = self.last_relevant(output, length_input)
        W2 = tf.Variable(np.random.rand(state_size, num_classes), dtype=tf.float32)
        b2 = tf.Variable(np.zeros((num_classes)), dtype=tf.float32)
        
        prediction = tf.nn.softmax(tf.matmul(last, W2) + b2)
        cross_entropy = -tf.reduce_sum(batchY_placeholder * tf.log(prediction))
        learning_rate = 0.003
        train_step = tf.train.AdagradOptimizer(learning_rate).minimize(cross_entropy)

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            loss_list = []
            for epoch_idx in range(num_epochs):
                _current_cell_state = np.zeros((batch_size, state_size))
                _current_hidden_state = np.zeros((batch_size, state_size))
                for i in range(20):
                    batchX = np.zeros((batch_size, backprop_length, input_dimensions))
                    batchY = np.zeros((batch_size, num_classes))
                    for j in range(batch_size):
                        r = np.random.randint(input_data_num)
                        batchX[j] = x[r]
                        batchY[j] = y[r]
                    _cross_entropy, _train_step, _current_state, _prediction =\
                    sess.run(
                    [cross_entropy, train_step, current_state, prediction],
                    feed_dict={
                        batchX_placeholder: batchX,
                        batchY_placeholder: batchY,
                        cell_state: _current_cell_state,
                        hidden_state: _current_cell_state
                    })
                    _current_cell_state, _current_hidden_state = _current_state
                    loss_list.append(_cross_entropy)
                    if i % 10 == 0:
                        print("Step", i, "loss", _cross_entropy)
            print("training finished.")
            self.saver = tf.train.Saver()
            self.saver.save(sess, "./tmp/model.ckpt")


    def length(self, seq):
        used = tf.sign(tf.reduce_max(tf.abs(seq), reduction_indices=2))
        length = tf.reduce_sum(used, reduction_indices=1)
        length = tf.cast(length, tf.int32)
        return length


    def last_relevant(self, output, length_input):
        batch_size = tf.shape(output)[0]
        max_length = int(output.get_shape()[1])
        output_size = int(output.get_shape()[2])
        index = tf.range(0, batch_size) * max_length + (length_input - 1)
        flat = tf.reshape(output, [-1, output_size])
        relevant = tf.gather(flat, index)
        return relevant

        
    def generateData(self):
        '''
        x is shaped (input_data_num x max length x input dimensions)
        for singlex in x:
        singlex is shaped (max_input_length x input_dimensions)
        it holds info about a single input
        each (input_dimensions)-shaped vector represents a character as a
        one-hot vector.
        But it will be a zero vector if the input is shorter than
        max_input_length.

        y is shaped (input_data_num x input_dimensions)
        It holds as one-hot vectors the correct classification for each input.backprop_length
        '''
        fm = FilesManager()
        ps = Parser()
        dataset = fm.load_dataset(self.botname)
        dataset = [[ps.sentence2vecs(line[0]), line[1]] for line in dataset]
        lengths = [line[0].shape[0] for line in dataset]  # list of how long each sentences is
        print("lengths of each sentence is ", lengths)
        max_input_length = max(lengths)
        input_data_num = len(lengths)
        input_dimensions = dataset[0][0].shape[1]
        print("max length\t", max_input_length)
        print("input data num\t", input_data_num)
        print("input dimensions\t", input_dimensions)
        x = np.zeros((input_data_num, max_input_length, input_dimensions))
        for i in range(input_data_num):
            for j in range(dataset[i][0].shape[0]):
                x[i,j] = dataset[i][0][j]

        y_values = [line[1] for line in dataset]
        num_classes = max(y_values) + 1  # because aRraYS StaRT aT ZeRo
    
        y = np.zeros((input_data_num, num_classes))
        for i in range(input_data_num):
            y[i,dataset[i][1]] = 1.0
        return x, y

if __name__ == "__main__":
    nn = NeuralNetwork("okan")
    nn.train()
