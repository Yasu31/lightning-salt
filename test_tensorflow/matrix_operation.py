from __future__ import print_function
# import matplotlib
# import matplotlib.pyplot as plt
import tensorflow as tf
import time
'''
based on https://medium.com/@erikhallstrm/hello-world-tensorflow-649b15aed18c
runs dot operations on large matrices.
Would be a lot faster on a GPU, but there isn't one on the macbook pro...
'''


def get_times(maximum_time):
    matrix_sizes = range(500, 50000, 50)
    device_times = []
    # 500, 550, 600, ...
    for size in matrix_sizes:
        device_name = "/cpu:0"
        print("####### Calculating on the CPU #######")
        shape = (size, size)
        data_type = tf.float16
        with tf.device(device_name):
            r1 = tf.random_uniform(
                shape=shape, minval=0, maxval=1, dtype=data_type)
            r2 = tf.random_uniform(
                shape=shape, minval=0, maxval=1, dtype=data_type)
            dot_operation = tf.matmul(r2, r1)
        with tf.Session(config=tf.ConfigProto(log_device_placement=True))\
                as session:
            start_time = time.time()
            result = session.run(dot_operation)
            time_taken = time.time() - start_time
            print(result)
            device_times.append(time_taken)
        print(device_times)
        if time_taken > maximum_time:
            return device_times, matrix_sizes


device_times, matrix_sizes = get_times(1.5)
print(device_times)

# plt.plot(matrix_sizes[:len(gpu_times)], gpu_times, 'o-')
# plt.plot(matrix_sizes[:len(cpu_times)], cpu_times, 'o-')
# plt.ylabel('Time')
# plt.xlabel('Matrix size')
# plt.show()
