import tensorflow as tf
import tensorflow_datasets as tfds

dataset = tfds.load("mnist", split=tfds.Split.TRAIN)
dataset = tfds.load("cats_vs_dogs", split=tfds.Split.TRAIN, as_supervised=True)
dataset = tfds.load("tf_flowers", split=tfds.Split.TRAIN, as_supervised=True)