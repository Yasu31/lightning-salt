from __future__ import print_function, division
import numpy as np
import tensorflow as tf

num_epochs = 100
total_series_length = 50000
truncated_backprop_length = 15
state_size = 4
num_classes = 2
echo_step = 3
batch_size = 5
num_batches = total_series_length // batch_size // truncated_backprop_length


def generateData():
    x = np.array(np.random.choice(2, total_series_length, p=[0.5, 0.5]))
    # x is a vector containing 0 or 1, of length "total_series_length"
    # [0, 1, 0, 1, 1, ....]
    y = np.roll(x, echo_step)
    # np.roll shifts the elements of array x, echo_step steps to the right.
    y[0:echo_step] = 0

    x = x.reshape((batch_size, -1))
    y = y.reshape((batch_size, -1))
    # reshapes the array so that it has batch_size rows
    # and (total_series_length/batch_size) columns
    print(x.shape)
    return (x, y)


# the batch data are fed into the variables on each run.
batchX_placeholder = tf.placeholder(
    tf.float32, [batch_size, truncated_backprop_length])
batchY_placeholder = tf.placeholder(
    tf.int32, [batch_size, truncated_backprop_length])
cell_state = tf.placeholder(tf.float32, [batch_size, state_size])
hidden_state = tf.placeholder(tf.float32, [batch_size, state_size])
init_state = tf.contrib.rnn.LSTMStateTuple(cell_state, hidden_state)

W2 = tf.Variable(np.random.rand(state_size, num_classes), dtype=tf.float32)
b2 = tf.Variable(np.zeros((1, num_classes)), dtype=tf.float32)

# unpack columns
inputs_series = tf.split(batchX_placeholder, truncated_backprop_length, 1)
# tf.split(value, num_or_size_splits, axis=0) splist the tensor axis-wise.
# here, it splits the batchX_placeholder into truncated_backprop_length pieces
# therefore, tensors of size (batch_size, 1)
labels_series = tf.unstack(batchY_placeholder, axis=1)

# Forward passes
cell = tf.contrib.rnn.BasicLSTMCell(state_size, state_is_tuple=True)
states_series, current_state = tf.nn.static_rnn(
    cell, inputs_series, init_state)

logits_series = [tf.matmul(state, W2) + b2 for state in states_series]
predictions_series = [tf.nn.softmax(logits) for logits in logits_series]

losses = [tf.nn.sparse_softmax_cross_entropy_with_logits(
    logits=logits, labels=labels) for logits, labels in zip(logits_series, labels_series)]
total_loss = tf.reduce_mean(losses)

train_step = tf.train.AdagradOptimizer(0.3).minimize(total_loss)

with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    loss_list = []
    for epoch_idx in range(num_epochs):
        x, y = generateData()
        _current_cell_state = np.zeros((batch_size, state_size))
        _current_hidden_state = np.zeros((batch_size, state_size))
        print("new data, epoch", epoch_idx)
        for batch_idx in range(num_batches):
            start_idx = batch_idx * truncated_backprop_length
            end_idx = start_idx + truncated_backprop_length
            batchX = x[:, start_idx:end_idx]
            batchY = y[:, start_idx:end_idx]

            _total_loss, _train_step, _current_state, _predictions_series = \
                sess.run(
                    [total_loss, train_step, current_state, predictions_series],
                    feed_dict={
                        batchX_placeholder: batchX,
                        batchY_placeholder: batchY,
                        cell_state: _current_cell_state,
                        hidden_state: _current_hidden_state
                    })
            _current_cell_state, _current_hidden_state = _current_state
            loss_list.append(_total_loss)
            if batch_idx % 100 == 0:
                print("Step", batch_idx, "Batch loss", _total_loss)
