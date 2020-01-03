from __future__ import print_function

import argparse
import functools
import itertools
import os
import os.path as ops
import sys
import time

import numpy as np
import tensorflow as tf
import pprint

import six
from six.moves import xrange  # pylint: disable=redefined-builtin

sys.path.append('/data/')

from crnn_model import crnn_model
from local_utils import data_utils, log_utils, tensorboard_vis_summary
from global_configuration import config
from uaitrain.arch.tensorflow import uflag

from tensorflow.core.framework import node_def_pb2
from tensorflow.python.framework import device as pydev
from tensorflow.python.training import device_setter

from typing import List 
from PIL import Image
import cv2

def _tower_fn(feature):
    '''
    The l_size should be compatable with the train_shadownet_multi.py --l_size param
    This is also related with the 
    '''
    l_size=10
    shadownet = crnn_model.ShadowNet(phase='Train', hidden_nums=256, layers_nums=2, seq_length=l_size,
                                     num_classes=config.cfg.TRAIN.CLASSES_NUMS, rnn_cell_type='lstm')

    imgs = tf.image.resize_images(feature, (32, l_size*4), method=0)
    input_imgs = tf.cast(x=imgs, dtype=tf.float32)

    with tf.variable_scope('shadow', reuse=False):
        net_out, tensor_dict = shadownet.build_shadownet(inputdata=input_imgs)

    return net_out, tensor_dict, l_size

def get_words_from_chars(characters_list: List[str], sequence_lengths: List[int], name='chars_conversion'):
    with tf.name_scope(name=name):
        def join_charcaters_fn(coords):
            return tf.reduce_join(characters_list[coords[0]:coords[1]])

        def coords_several_sequences():
            end_coords = tf.cumsum(sequence_lengths)
            start_coords = tf.concat([[0], end_coords[:-1]], axis=0)
            coords = tf.stack([start_coords, end_coords], axis=1)
            coords = tf.cast(coords, dtype=tf.int32)
            return tf.map_fn(join_charcaters_fn, coords, dtype=tf.string)

        def coords_single_sequence():
            return tf.reduce_join(characters_list, keep_dims=True)

        words = tf.cond(tf.shape(sequence_lengths)[0] > 1,
                        true_fn=lambda: coords_several_sequences(),
                        false_fn=lambda: coords_single_sequence())

        return words

def get_shadownet_fn():
    def _shadownet_fun(features, labels, mode): 
        with tf.variable_scope('shadownet'):
            with tf.name_scope('tower_0') as name_scope:
                preds, tensor_dict, seq_len = _tower_fn(features['feature'])

        batch_size = tf.shape(features['feature'])[0]
        decoded, log_prob = tf.nn.ctc_beam_search_decoder(preds, seq_len*tf.ones([batch_size], dtype=tf.int32), merge_repeated=False)
        sequence_lengths_pred = tf.bincount(tf.cast(decoded[0].indices[:, 0], tf.int32))

        with tf.name_scope('code2str_conversion'):
            features = data_utils.FeatureIO(
                '/data/data/char_dict/char_dict.json',
                '/data/data/char_dict/ord_2_index_map.json',
                '/data/data/char_dict/index_2_ord_map.json')
            keys = features.get_idx2ord().keys()
            keys = list(map(int, keys))
            keys = tf.cast(keys, tf.int32)
            values = features.get_idx2ord().values()
            values = list(map(int, values))
            values = tf.cast(values, tf.int32)
            table_int2str = tf.contrib.lookup.HashTable(
                     tf.contrib.lookup.KeyValueTensorInitializer(keys, values), -1)

        preds = table_int2str.lookup(tf.cast(decoded[0], tf.int32))
        word_keys = features.get_char_list().keys()
        word_keys = list(map(int, word_keys))
        word_keys = tf.cast(word_keys, tf.int64)
        word_values = features.get_char_list().values()
        word_values = list(map(str, word_values))
        table_str2word = tf.contrib.lookup.HashTable(
            tf.contrib.lookup.KeyValueTensorInitializer(word_keys, word_values), "")

        values = tf.cast(preds.values, tf.int64)
        words = table_str2word.lookup(values)
        words = get_words_from_chars(words, sequence_lengths_pred)

        predictions = {
            'words' : words,
            'length' : sequence_lengths_pred,
            'pred': preds.values,
            'decoded': decoded[0].values,
        }

        export_outputs = {
            'prediction': tf.estimator.export.PredictOutput(predictions)
        }

        return tf.estimator.EstimatorSpec(
            mode=mode,
            predictions=predictions,
            export_outputs=export_outputs)

    return _shadownet_fun

class crnnPredictor():
    def __init__(self, model_dir):
        self._model_dir = model_dir
        self.output = {}

    def build_crnn_model(self):
        sess_config = tf.ConfigProto(
            allow_soft_placement=True,
            gpu_options=tf.GPUOptions(force_gpu_compatible=True))

        run_config = tf.contrib.learn.RunConfig(session_config=sess_config, model_dir=self._model_dir)

        classifier = tf.estimator.Estimator(
            model_fn=get_shadownet_fn(),
            config=run_config)
        self._classifier = classifier

    def do_serve_predict(self, raw_images):
        images = []
        for image in raw_images:
            image = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            image = cv2.resize(image, (200, 32))
            image = np.expand_dims(image, axis=0).astype(np.float32)
            image = image.reshape((32, 200, 3)).astype(np.uint8)
            images.append(image)
        
        sess = self.output['sess']
        input_tensor = self.output['input_tensor']
        output_tensor = self.output['output_tensor']

        output_tensor = sess.run(output_tensor, feed_dict={input_tensor: np.array(images)})
        return output_tensor                                                                                                                                   
                                                                                                                                                               
    def load_serve_model(self):                                                                                                                                
        sess = tf.Session()

        """
        You can use 
            saved_model_cli show --dir /tmp/saved_model_dir
            to inspect the saved model for tag-set and signatures
            refer to https://www.tensorflow.org/guide/saved_model#using_savedmodel_with_estimators for more details
        """
        tag = 'serve'
        meta_graph_def = tf.saved_model.loader.load(sess, [tag], self._model_dir)
        signature = meta_graph_def.signature_def
        
        sig = 'prediction'
        input_key = 'input'
        input_tensor_name = signature[sig].inputs[input_key].name
        input_tensor = sess.graph.get_tensor_by_name(input_tensor_name)

        output_key = 'words'
        output_tensor_name = signature[sig].outputs[output_key].name
        output_tensor = sess.graph.get_tensor_by_name(output_tensor_name)

        self.output['sess'] = sess
        self.output['input_tensor'] = input_tensor
        self.output['output_tensor'] = output_tensor

    def export_model(self):
        def serving_input_reciver_fn():
            """ 
            You should change the shape of this placeholder according to your request
            This shape is compatable with do_serve_predict()
            """
            serialized_tf_example = tf.placeholder(shape=[None, 32, 200, 3], dtype=tf.uint8)
            return tf.estimator.export.ServingInputReceiver(serialized_tf_example, serialized_tf_example)

        self._classifier.export_savedmodel('./checkpoint_dir', serving_input_reciver_fn)

if __name__ == '__main__':
    predictor = crnnPredictor('./checkpoint_dir')
    predictor.build_crnn_model()
    predictor.export_model()
