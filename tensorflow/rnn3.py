from __future__ import print_function, division
import numpy as np
import tensorflow as tf

num_epochs = 200
max_input_length = 15  # maximum num of chacacters in the training data messages
input_dimensions = 10  # how many types of characters there are
input_data_num = 100  # how many different training data
backprop_length = max_input_length
state_size = 100
num_classes = 10  # how many types of output classes? (how many responses?)
batch_size = 5


def generateData():
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

    Currently, both x and y are generated randomly.
    '''
    x = np.zeros((input_data_num, max_input_length, input_dimensions))
    for singlex in x:
        input_length = np.random.randint(2, max_input_length)
        for singlevector in singlex[0:input_length, :]:
            singlevector[np.random.randint(input_dimensions)] = 1
    y = np.zeros((input_data_num, num_classes))
    for singley in y:
        singley[np.random.randint(num_classes)] = 1
    return x, y


def length(seq):
    used = tf.sign(tf.reduce_max(tf.abs(seq), reduction_indices=2))
    length = tf.reduce_sum(used, reduction_indices=1)
    length = tf.cast(length, tf.int32)
    return length


def last_relevant(output, length_input):
    batch_size = tf.shape(output)[0]
    max_length = int(output.get_shape()[1])
    output_size = int(output.get_shape()[2])
    index = tf.range(0, batch_size) * max_length + (length_input - 1)
    flat = tf.reshape(output, [-1, output_size])
    relevant = tf.gather(flat, index)
    return relevant


batchX_placeholder = tf.placeholder(
    tf.float32, [batch_size, backprop_length, input_dimensions])
batchY_placeholder = tf.placeholder(tf.float32, [batch_size, num_classes])
cell_state = tf.placeholder(tf.float32, [batch_size, state_size])
hidden_state = tf.placeholder(tf.float32, [batch_size, state_size])
init_state = tf.contrib.rnn.LSTMStateTuple(cell_state, hidden_state)
length_input = length(batchX_placeholder)
output, current_state = tf.nn.dynamic_rnn(tf.contrib.rnn.BasicLSTMCell(state_size, state_is_tuple=True),
                                          batchX_placeholder, dtype=tf.float32, sequence_length=length_input)
last = last_relevant(output, length_input)
W2 = tf.Variable(np.random.rand(state_size, num_classes), dtype=tf.float32)
b2 = tf.Variable(np.zeros((num_classes)), dtype=tf.float32)

prediction = tf.nn.softmax(tf.matmul(last, W2) + b2)
cross_entropy = -tf.reduce_sum(batchY_placeholder * tf.log(prediction))
learning_rate = 0.003
train_step = tf.train.AdagradOptimizer(learning_rate).minimize(cross_entropy)

with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    loss_list = []
    x, y = generateData()
    for epoch_idx in range(num_epochs):
        _current_cell_state = np.zeros((batch_size, state_size))
        _current_hidden_state = np.zeros((batch_size, state_size))
        for i in range(100):
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
