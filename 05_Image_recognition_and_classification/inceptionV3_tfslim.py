
# coding: utf-8

# # InceptionV3 示例 - TensorLayer结合TF-Slim实现

# In[1]:


import tensorflow as tf
import tensorlayer as tl
slim = tf.contrib.slim
from tensorflow.contrib.slim.python.slim.nets.alexnet import alexnet_v2
from tensorflow.contrib.slim.python.slim.nets.inception_v3 import inception_v3_base, inception_v3, inception_v3_arg_scope
# from tensorflow.contrib.slim.python.slim.nets.resnet_v2 import resnet_v2_152
# from tensorflow.contrib.slim.python.slim.nets.vgg import vgg_16
import skimage
import skimage.io
import skimage.transform
import time, os
from data.imagenet_classes import *
import numpy as np


# In[2]:


# 可能需要从下载模型文件
import os.path
if not os.path.isfile('./inception_v3.ckpt'):
    get_ipython().system('wget -O inception_v3.tar.gz http://download.tensorflow.org/models/inception_v3_2016_08_28.tar.gz')
    get_ipython().system('tar -zxvf inception_v3.tar.gz')


# ## 载入图像数据

# In[3]:


def load_image(path):
    # load image
    img = skimage.io.imread(path)
    img = img / 255.0
    assert (0 <= img).all() and (img <= 1.0).all()
    # print "Original Image Shape: ", img.shape
    # we crop image from center
    short_edge = min(img.shape[:2])
    yy = int((img.shape[0] - short_edge) / 2)
    xx = int((img.shape[1] - short_edge) / 2)
    crop_img = img[yy: yy + short_edge, xx: xx + short_edge]
    # resize to 299, 299
    resized_img = skimage.transform.resize(crop_img, (299, 299))
    return resized_img


# In[4]:


def print_prob(prob):
    synset = class_names
    # print prob
    pred = np.argsort(prob)[::-1]
    # Get top1 label
    top1 = synset[pred[0]]
    print("Top1: ", top1, prob[pred[0]])
    # Get top5 label
    top5 = [(synset[pred[i]], prob[pred[i]]) for i in range(5)]
    print("Top5: ", top5)
    return top1


# In[5]:


## Alexnet_v2 / All TF-Slim nets can be merged into TensorLayer
# x = tf.placeholder(tf.float32, shape=[None, 299, 299, 3])
# net_in = tl.layers.InputLayer(x, name='input_layer')
# network = tl.layers.SlimNetsLayer(layer=net_in, slim_layer=alexnet_v2,
#                                 slim_args= {
#                                        'num_classes' : 1000,
#                                        'is_training' : True,
#                                        'dropout_keep_prob' : 0.5,
#                                        'spatial_squeeze' : True,
#                                        'scope' : 'alexnet_v2'
#                                         },
#                                     name='alexnet_v2'  # <-- the name should be the same with the ckpt model
#                                     )
# sess = tf.InteractiveSession()
# # sess.run(tf.initialize_all_variables())
# tl.layers.initialize_global_variables(sess)
# network.print_params()


# ## 将TF-Slim的网络结构嵌入到TensorLayer中

# In[6]:


# network.print_params()


## InceptionV3 / All TF-Slim nets can be merged into TensorLayer
x = tf.placeholder(tf.float32, shape=[None, 299, 299, 3])
net_in = tl.layers.InputLayer(x, name='input_layer')
with slim.arg_scope(inception_v3_arg_scope()):
    ## Alternatively, you should implement inception_v3 without TensorLayer as follow.
    # logits, end_points = inception_v3(X, num_classes=1001,
    #                                   is_training=False)
    network = tl.layers.SlimNetsLayer(layer=net_in, slim_layer=inception_v3,
                                    slim_args= {
                                             'num_classes' : 1001,
                                             'is_training' : False,
                                            #  'dropout_keep_prob' : 0.8,       # for training
                                            #  'min_depth' : 16,
                                            #  'depth_multiplier' : 1.0,
                                            #  'prediction_fn' : slim.softmax,
                                            #  'spatial_squeeze' : True,
                                            #  'reuse' : None,
                                            #  'scope' : 'InceptionV3'
                                            },
                                        name='InceptionV3'  # <-- the name should be the same with the ckpt model
                                        )


# ## 运行

# In[7]:


sess = tf.InteractiveSession()

network.print_params(False)

saver = tf.train.Saver()
if not os.path.isfile("inception_v3.ckpt"):
    print("请从 https://github.com/tensorflow/models/tree/master/research/slim#pre-trained-models 下载 inception_v3 模型文件")
    exit()
try:    # TF12+
    saver.restore(sess, "./inception_v3.ckpt")
except: # TF11
    saver.restore(sess, "inception_v3.ckpt")
print("Model Restored")

from scipy.misc import imread, imresize
y = network.outputs
probs = tf.nn.softmax(y)
img1 = load_image("data/puzzle.jpeg")
img1 = img1.reshape((1, 299, 299, 3))

start_time = time.time()
prob = sess.run(probs, feed_dict= {x : img1})
print("End time : %.5ss" % (time.time() - start_time))
print_prob(prob[0][1:]) # Note : as it have 1001 outputs, the 1st output is nothing


## 训练好的模型可以存为 npz 文件
# tl.files.save_npz(network.all_params, name='model_inceptionV3.npz')

