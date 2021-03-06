import numpy as np
import tensorflow as tf
from baselines.a2c.utils import conv, fc, conv_to_fc, batch_to_seq, seq_to_batch, lstm
from baselines.common.distributions import make_pdtype
from baselines.common.input import observation_input

from coinrun.config import Config

def impala_cnn(images, depths=[16, 32, 32]):
    """
    Model used in the paper "IMPALA: Scalable Distributed Deep-RL with 
    Importance Weighted Actor-Learner Architectures" https://arxiv.org/abs/1802.01561
    """
    use_batch_norm = Config.USE_BATCH_NORM == 1

    dropout_layer_num = [0]
    dropout_assign_ops = []

    def dropout_layer(out):
        if Config.DROPOUT > 0:
            out_shape = out.get_shape().as_list()
            num_features = np.prod(out_shape[1:])

            var_name = 'mask_' + str(dropout_layer_num[0])
            batch_seed_shape = out_shape[1:]
            batch_seed = tf.get_variable(var_name, shape=batch_seed_shape, initializer=tf.random_uniform_initializer(minval=0, maxval=1), trainable=False)
            batch_seed_assign = tf.assign(batch_seed, tf.random_uniform(batch_seed_shape, minval=0, maxval=1))
            dropout_assign_ops.append(batch_seed_assign)

            curr_mask = tf.sign(tf.nn.relu(batch_seed[None,...] - Config.DROPOUT))

            curr_mask = curr_mask * (1.0 / (1.0 - Config.DROPOUT))

            out = out * curr_mask

        dropout_layer_num[0] += 1

        return out

    def conv_layer(out, depth):
        out = tf.layers.conv2d(out, depth, 3, padding='same')
        out = dropout_layer(out)

        if use_batch_norm:
            out = tf.contrib.layers.batch_norm(out, center=True, scale=True, is_training=True)

        return out

    def residual_block(inputs):
        depth = inputs.get_shape()[-1].value
        
        out = tf.nn.relu(inputs)

        out = conv_layer(out, depth)
        out = tf.nn.relu(out)
        out = conv_layer(out, depth)
        return out + inputs

    def conv_sequence(inputs, depth):
        out = conv_layer(inputs, depth)
        out = tf.layers.max_pooling2d(out, pool_size=3, strides=2, padding='same')
        out = residual_block(out)
        out = residual_block(out)
        return out

    out = images
    for depth in depths:
        out = conv_sequence(out, depth)

    out = tf.layers.flatten(out)
    out = tf.nn.relu(out)
    out = tf.layers.dense(out, 256, activation=tf.nn.relu)

    return out, dropout_assign_ops

def nature_cnn(scaled_images, **conv_kwargs):
    """
    Model used in the paper "Human-level control through deep reinforcement learning" 
    https://www.nature.com/articles/nature14236
    """

    def activ_1(curr):
        return tf.nn.relu(curr)

    def activ_2(curr):
        out = tf.nn.relu(curr)
        out = tf.layers.max_pooling2d(out, pool_size=3, strides=2, padding='VALID') # Maybe try pool_size = 3, also padding = 'SAME', as per the IMPALA architecture.
        return out
        #return tf.nn.max_pool(tf.nn.relu(curr), [1, 2, 2, 1], [1, 2, 2, 1], 'VALID')


        #out = tf.layers.max_pooling2d(out, pool_size=3, strides=2, padding='same')

       #self.pool_old = nn.MaxPool2d(2, 2) # kernel size, stride


    # FOR NATURE CNN:
    # total num params: 604840

    # FOR ARCH BELOW:
    # total num params: 598780

    #h = activ(conv(scaled_images, 'c1', nf=32, rf=8, stride=4, init_scale=np.sqrt(2), **conv_kwargs))
    #h2 = activ(conv(h, 'c2', nf=64, rf=4, stride=2, init_scale=np.sqrt(2), **conv_kwargs))
    #h3 = activ(conv(h2, 'c3', nf=64, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    #h3 = conv_to_fc(h3)

    h11 = activ_1(conv(scaled_images, 'c11', nf=16, rf=8, stride=4, init_scale=np.sqrt(2), **conv_kwargs))
    h12 = activ_1(conv(h11, 'c12', nf=32, rf=4, stride=2, init_scale=np.sqrt(2), **conv_kwargs))
    h13 = activ_1(conv(h12, 'c13', nf=32, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    h13 = conv_to_fc(h13)

    h21 = activ_2(conv(scaled_images, 'c21', nf=12, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs)) # I *think* IMPALA uses rf = 3 everywhere
    h22 = activ_2(conv(h21, 'c22', nf=12, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    h23 = activ_2(conv(h22, 'c23', nf=24, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    #h24 = activ_2(conv(h23, 'c24', nf=32, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    h24 = conv_to_fc(h23)


    # out_channels = nf
    # kernel_size = rf
    # stride = stride


    #self.conv11 = nn.Conv2d(in_channels=in_channels, out_channels=21, kernel_size=8, stride=4)
    #self.conv12 = nn.Conv2d(in_channels=21, out_channels=42, kernel_size=4, stride=2)
    #self.conv13 = nn.Conv2d(in_channels=42, out_channels=42, kernel_size=3, stride=1)
        
    # Architecture taken from here: https://github.com/Nasdin/ReinforcementLearning-AtariGame
    #self.conv21 = nn.Conv2d(in_channels=in_channels, out_channels=32, kernel_size=5, stride=1, padding=2)
    #self.conv22 = nn.Conv2d(in_channels=32, out_channels=32, kernel_size=5, stride=1, padding=1)
    #self.conv23 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=4, stride=1, padding=1)
    #self.conv24 = nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1)

    #self.fc1 = nn.Linear(in_features=7*7*42 + 4*4*64, out_features=512)

    #print('scaled_images shape = ', scaled_images.get_shape()) # for some reason it's 4*4*42 + 1*1*64
    #print('h13 shape = ', h13.get_shape())
    #print('h24 shape = ', h24.get_shape())
    #print('a' + 0)
    h_cat = tf.concat([h13, h24], 1)

    meh1 = fc(h_cat, 'fc1', nh=512, init_scale=np.sqrt(2))

    #meh2 = fc(h24, 'fc21', nh=256, init_scale=np.sqrt(2))
    #print('shape = ', meh1.get_shape())

    #meh_concat = tf.concat([meh1, meh2], 1)

    return activ_1(meh1)

def choose_cnn(images):
    arch = Config.ARCHITECTURE
    scaled_images = tf.cast(images, tf.float32) / 255.
    dropout_assign_ops = []

    if arch == 'nature':
        out = nature_cnn(scaled_images)
    elif arch == 'impala':
        out, dropout_assign_ops = impala_cnn(scaled_images)
    elif arch == 'impalalarge':
        out, dropout_assign_ops = impala_cnn(scaled_images, depths=[32, 64, 64, 64, 64])
    else:
        assert(False)

    return out, dropout_assign_ops

class LstmPolicy(object):

    def __init__(self, sess, ob_space, ac_space, nbatch, nsteps, nlstm=256):
        nenv = nbatch // nsteps
        self.pdtype = make_pdtype(ac_space)
        X, processed_x = observation_input(ob_space, nbatch)

        M = tf.placeholder(tf.float32, [nbatch]) #mask (done t-1)
        S = tf.placeholder(tf.float32, [nenv, nlstm*2]) #states
        with tf.variable_scope("model", reuse=tf.AUTO_REUSE):
            h, self.dropout_assign_ops = choose_cnn(processed_x)
            xs = batch_to_seq(h, nenv, nsteps)
            ms = batch_to_seq(M, nenv, nsteps)
            h5, snew = lstm(xs, ms, S, 'lstm1', nh=nlstm)
            h5 = seq_to_batch(h5)
            vf = fc(h5, 'v', 1)[:,0]
            self.pd, self.pi = self.pdtype.pdfromlatent(h5)

        a0 = self.pd.sample()
        neglogp0 = self.pd.neglogp(a0)
        self.initial_state = np.zeros((nenv, nlstm*2), dtype=np.float32)

        def step(ob, state, mask):
            return sess.run([a0, vf, snew, neglogp0], {X:ob, S:state, M:mask})

        def value(ob, state, mask):
            return sess.run(vf, {X:ob, S:state, M:mask})

        self.X = X
        self.M = M
        self.S = S
        self.vf = vf
        self.step = step
        self.value = value

class CnnPolicy(object):
    def __init__(self, sess, ob_space, ac_space, nbatch, nsteps, **conv_kwargs): #pylint: disable=W0613
        self.pdtype = make_pdtype(ac_space)
        X, processed_x = observation_input(ob_space, nbatch)

        with tf.variable_scope("model", reuse=tf.AUTO_REUSE):
            h, self.dropout_assign_ops = choose_cnn(processed_x)
            vf = fc(h, 'v', 1)[:,0]
            self.pd, self.pi = self.pdtype.pdfromlatent(h, init_scale=0.01)

        a0 = self.pd.sample()
        neglogp0 = self.pd.neglogp(a0)
        self.initial_state = None

        def step(ob, *_args, **_kwargs):
            a, v, neglogp = sess.run([a0, vf, neglogp0], {X:ob})
            return a, v, self.initial_state, neglogp

        def value(ob, *_args, **_kwargs):
            return sess.run(vf, {X:ob})

        self.X = X
        self.vf = vf
        self.step = step
        self.value = value


def get_policy():
    use_lstm = Config.USE_LSTM
    
    if use_lstm == 1:
        policy = LstmPolicy
    elif use_lstm == 0:
        policy = CnnPolicy
    else:
        assert(False)

    return policy
