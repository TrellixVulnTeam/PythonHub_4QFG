# EAST Example
EAST example shows how to run tensorflow implementation of [EAST: An Efficient and Accurate Scene Text Detector](https://arxiv.org/abs/1704.03155v2) on UCloud AI Train Platform. The example is based on https://github.com/argman/EAST. We also provide a multi-gpu distriubted version in this example.

# Setup
You should prepare your own training data and pretrained model before running the task. As UAI Train nodes does not provide network access, you should prepare your data locally.

## Intro
We proivde two versions of EAST:
  1. Multi-gpu version (multigpu\_train.py). This version is compatable with the original argman's implementation. We only made necessary modifications for it to run in UAI Train platform.
  2. Multi-gpu Distributed version (distgpu\_train.py). This version is implemented with tf.Estimator API which can run on a distributed environment. It takes tfrecords as its input. You can use icdar\_tfrecord.py to build your own tfrecords.

This example directly use most of code in https://github.com/argman/EAST such as model.py, data\_util.py, nets.

## Preparing docker image
We have provided necessary code for you to build training docker for EAST as well as the dockerfile

### Multi-gpu UAI Example
We made the following modifications to the EAST code:

1.multigpu\_train.py

    # Line 7: Add UAI flag
    from uaitrain.arch.tensorflow import uflag

    # Line 72: 
    # checkpoint_path should under FLAGS.output_dir (/data/output/, the default 'UAI Train' output dir)
    # pretrained_model_path should under FLAGS.data_dir (/data/data/, the default 'UAI Train' data input dir)
    # gpus should get from FLAGS.num_gpus
    FLAGS.checkpoint_path=os.path.join(FLAGS.output_dir, FLAGS.checkpoint_path)
    if FLAGS.pretrained_model_path is not None:
        FLAGS.pretrained_model_path=os.path.join(FLAGS.data_dir, FLAGS.pretrained_model_path)
    gpus = list(range(FLAGS.num_gpus)) 

    # Line 170:
    # Add print train status every 100 steps
            if step % 100 == 0:
                end = time.time()
                avg_time_per_step = (end - start) / 100
                avg_examples_per_second = (100 * FLAGS.batch_size_per_gpu * len(gpus)) / (end - start)
                print('Step {:06d}, model loss {:.4f}, total loss {:.4f}, {:.2f} seconds/step, {:.2f} examples/second'.format(
                    step, ml, tl, avg_time_per_step, avg_examples_per_second))
                start = time.time()

2.icdar.py

    # Line 15: Add UAI flag
    from uaitrain.arch.tensorflow import uflag

    # Line 36: training_data_path should under FLAGS.data_dir (/data/data/, the default 'UAI Train' data input dir)
    FLAGS.training_data_path = os.path.join(FLAGS.data_dir, FLAGS.training_data_path)

We have provied these two modified files into east/code/.

#### Build the Docker images
We provide the basic Dockerfile east.Dockerfile to build the docker image for training east model.

You should put argman's EAST code into working path, and copy the icdar.py and multigpu\_train.py provided in this example to switch the original icdar.py and multigpu\_train.py.
You also should put the east.Dockerfile into the same directory of EAST code:

    /data/east/
    |  east.Dockerfile
    |  EAST/
    |  |_ data_util.py
    |  |_ icdar.py
    |  |_ multigpu_train.py
    |  | ...
    |  |_ nets/

We should run the docker build under PATH\_TO/east:

    # cd /data/east/
    # sudo docker build -f east.Dockerfile -t uhub.ucloud.cn/<YOUR_UHUB_REGISTRY>/east:test .
    
You can use any docker-name here if you want.

### Distributed EAST training
We also provide the distributed east version in distgpu\_train.py. It is a fresh implementation of distributed east training except using the same model defined in model.py. You can follow the [Build the Docker Image](#build-the-docker-images) to build your own distributed training docker image and follow the [Prepare tfrecord](#preparing-tfrecords-for-dist-training) to build the tfrecords for distributed training.

#### Build the Docker image
You should put argman's EAST code into working path, and copy the icdar\_dataset.py and distgpu\_train.py in this example to the same path. You also should put the east-dist.Dockerfile into the same directory of EAST code:

    /data/east/
    |  east-dist.Dockerfile
    |  EAST/
    |  |_ data_util.py
    |  |_ icdar_dataset.py
    |  |_ distgpu_train.py
    |  | ...
    |  |_ nets/

We should run the docker build cmd under PATH\_TO/east:

    # cd /data/east/
    # sudo docker build -f east-dist.Dockerfile -t uhub.ucloud.cn/<YOUR_UHUB_REGISTRY>/east-dist:test .
    
You can use any docker-name here if you want.

#### Using Pretrained ResNet50 Net
You can use the Resnet V1 50 provided by tensorflow slim [slim resnet v1 50](http://download.tensorflow.org/models/resnet_v1_50_2016_08_28.tar.gz) as the pretrained CNN part. We have provided the code to load the slim resnet50 checkpoint in distgpu\_train.py. In order to use it in distributed training, we suggest you to pack the Resnet50 checkpoint file into dockerfile (as the ps nodes can find the checkpoint file directly inside its docker image). You also should put the east-dist.Dockerfile into the same directory of EAST code:

    /data/east/
    |  east-dist.Dockerfile
    |  EAST/
    |  |_ data_util.py
    |  |_ icdar_dataset.py
    |  |_ distgpu_train.py
    |  | ...
    |  |_ nets/
    |  |_ resnet_v1_50.ckpt

We should run the docker build cmd under PATH\_TO/east:

    # cd /data/east/
    # sudo docker build -f east-dist.Dockerfile -t uhub.ucloud.cn/<YOUR_UHUB_REGISTRY>/east-dist:test .
    
You can use any docker-name here if you want.

## Preparing the Data
Please follow the https://github.com/argman/EAST/readme.md to download the training data and the pretrained model. The example use the ICDAR dataset.

### Create Local Test Data Path
Suppose you have downloaded the dataset and put both the IMG files and TXT files into one dir (e.g., ICDAR 2015):

    # cd /data/east/train-data/
    # ls
    img_1.jpg img_2.jpg ... img_1000.jpg
    img_1.txt img_2.txt ... img_1000.txt

### Using raw images for Dist Training
Distributing raw images/txts to each node in a distributed cluster is costy. We provide a simple way to distribute a tar-pack of raw images/txts to each node and uncompress it before training automatically. You can refer to icdar\_dataset.py to see how tar-pack is decompressed during EastDataSet initialization and how image/txt data is organized into data batches in EastDataSet->make\_batch().

To compress data, you can use:

    cd /data/east/
    tar -czf data.tar.gz train_data/

The resulting data.tar.gz is the compressed tar-pack of raw images/txts. After copying data.tar.gz to each node (The data.tar.gz should be put into the path of os.path.join(FLAGS.data\_dir, FLAGS.train\_dir), then we can use following args to tell icdar\_dataset model how to setup EastDataSet:

    --tarfile=data.tar.gz --tarpath=train_data/

**tarfile** refers to the name of the tar file and the **tarpath** refers to the sub-filedir inside the tar file.

**To use tar-pack data for training, distgpu\_train.py should import icdar_dataset instead of import icdar_tfrecord_dataset**

### Using tfrecords for Dist Training
You can also use tfrecords as data for distributed training. We provide icdar_tfrecord.py to generate tfrecords from raw images/txts. You can run it as follows:

    python icdar_tfrecord.py --training_data_path=<PATH-TO-DATA> --save_dir=./tfrecords --shards=10

It will generate both train_xxx.tfrecord and validation_xxx.tfrecord. It will take 90% of data into train set and 10% of data into validation set. You can modify the function write\_features to change this rate.

**Note:** Tfrecord generator is only compatable with python3. If you use python2, the generated tfrecords will be broken.

**Note:** Only distgpu\_train.py is compatable with tfrecords. You can also use distgpu\_train.py in single node training. 

**To use tfrecords for training, distgpu\_train.py should import icdar_tfrecord_dataset instead of import icdar_dataset**

## Run the train
We can simply use the following cmd to run the local test.(GPU version)

    sudo nvidia-docker run -it -v /data/east/:/data/data -v /data/east/output:/data/output uhub.service.ucloud.cn/uaishare/tf-east:tf-1.5 /bin/bash -c "cd /data&&python /data/multigpu_train.py --num_gpus=1 --input_size=512 --batch_size_per_gpu=8 --text_scale=512 --training_data_path=train_data --geometry=RBOX --learning_rate=0.0001 --num_readers=24 --pretrained_model_path=resnet_v1_50.ckpt --data_dir=/data/data/ --output_dir=/data/output --checkpoint_path=east_icdar2015_resnet_v1_50_rbox
    
You can use the same image to run the training on UAI Train Platform. For more details please see https://docs.ucloud.cn/ai/uai-train.

## Training with distributed multi-gpu
The distgpu\_train.py can be directly used in distributed training envs. (By default, it uses tar-pack of raw images/txts as input)

UAI Train Platform can dynamicaaly deploy the training cluster and generate the TF\_CONFIG for each training node. You only need to run the training cmd as:

    /data/distgpu_train.py --batch_size=128 --max_steps=2000 --tarfile=data.tar.gz --tarpath=train_data/

To use the pretrained resnet50 model, you can run the training cmd as(Suppose you have packed the resnet ckpt file into docker image as suggested in [Using Pretrained ResNet50 Net](#using-pretrained-resnet50-net)):

    /data/distgpu_train.py --batch_size=128 --max_steps=2000 --pretrained_model_path=./resnet_v1_50.ckpt --tarfile=data.tar.gz --tarpath=train_data/

For more details please see https://docs.ucloud.cn/ai/uai-train.
