# Imagenet Example

Imagenet example includes image classification code for training on imagenet dataset.                                                                                                      

## Setup

You should follow https://github.com/apache/incubator-mxnet/tree/master/example/image-classification to download and generate your own imagenet dataset

We suggest you to use the im2rec.py tool to generate .rec file with chuncks. The following cmd will genereate 1024 mxnet\_\*\_train.rec and 1024 mxnet\_\*\_val.rec files

	$ python tools/im2rec.py --resize 480 --quality 95 --num-thread 8 /mnt/imagenet/mxnet/ /mnt/imagenet/raw-data/train/ --chunks 1024
	$ mv /mnt/imagenet/mxnet/train/mxnet_*_train.rec /mnt/imagenet/mxnet/train_rec/
	$ mv /mnt/imagenet/mxnet/val/mxnet_*_val.rec /mnt/imagenet/mxnet/val_rec/

## Intro

The main body of the resnet code is following the https://github.com/apache/incubator-mxnet/blob/master/example/image-classification/train\_imagenet.py

But we made appropriate modifications to run it on UAI platform.

## UAI Example  
                                                                                                                                               
We do following modifications to following files: train\_imagenet.py, common/fit.py
                                                                                                        
1. Add UAI SDK related arguments: --data\_dir, --output\_dir, --work\_dir, --log\_dir, --num\_gpus by adding following codes:

	```python
		from uaitrain.arch.mxnet import uargs
		
		if __name__ == '__main__':
		    ...
		    uargs.add_uai_args(parser)
		    ...
	```
these arguments are auto generated by UAI Train Platform, see: https://github.com/ucloud/uai-sdk/blob/master/uaitrain/arch/mxnet/uargs.py for more details 
                                                             
2. Modify code to use UAI arguments: 
  
  - Add UAI output_dir path
	
	```python
	   fit.py L47:
	   def _load_model(args, rank=0):
	     ...
		  model_prefix = os.path.join(args.output_dir, args.model_prefix)
		  
		fit.py L60:
		def _save_model(args, rank=0):
		  ...
		  model_prefix = os.path.join(args.output_dir, args.model_prefix)
	``` 

  - Use args.num_gpus for gpu cnts
 
 ```python
   fit.py L165:
   def fit(args, network, data_loader, **kwargs):
     # devices for training
     # Add UAI multi-gpu dev support
     devs = mx.cpu() if args.num_gpus is None or args.num_gpus is 0 else [
        mx.gpu(i) for i in range(args.num_gpus)]
  ``` 

3. Use /data/data/ for data input inside the UAI MXNet Docker

## How to run
We assume you fully understand how UAI Train docker image works and has already reads the DOCS here: https://docs.ucloud.cn/ai/uai-train/guide/tensorflow

1. Pack the imagenet example code into docker using mxtne\_tools.py provided in https://github.com/ucloud/uai-sdk/blob/master/uaitrain\_tool/mxnet/
2. Run the docker locally or push it into UAI Train platform to run.

Node: We put data into /mnt/imagenet/mxnet/train-rec/ and /mnt/imagenet/mxnet/val-rec/
   
#### The simplest CMD applied to run is 

     /usr/bin/python /data/train_imagenet.py --batch-size 32 --image-shape 3,299,299 --num-epochs 1 --kv-store device --data-train=/data/data/train-rec/ --data-val=/data/data/val-rec/

#### An pack cmd example is:

    sudo python mxnet_tool.py pack --public_key=<UCLOUD_PUB_KEY> \ 
    --private_key=<UCLOUD_PRIV_KEY> \
    --code_path=code/ \
    --mainfile_path=train_imagenet.py \
    --uhub_username=<UCLOUD_ACCOUNT> \
    --uhub_password=<UCLOUD_ACCOUNT_PASSWD> \
    --uhub_registry=<UHUB_DOCKER_REGISTRY> \
    --uhub_imagename=resnet-imagenet-mxnet \
    --ai_arch_v=mxnet-1.0.0 \
    --test_data_path=<LOCAL_PATH_TO_IMAGENET_DATA_FOR_TEST> \
    --test_output_path=<LOCAL_PATH_TO_OUTOUT_FOR_TEST> \
    --train_params="--batch-size 32 --image-shape 3,299,299 --num-epochs 1 --kv-store device --data-train=/data/data/train-rec/ --data-val=/data/data/val-rec/"
   
Note: 
The tfrecords should stored in LOCAL\_PATH\_TO\_IMAGENET\_DATA\_FOR\_TEST in this example for loacal test

### Performance
System configuration

| Config      |      Value         |
| ----------- | -------------------|
| MXNet       |  1.0.0             |
| batch\_size | 32 for each GPU    |


Performance Result

| Model                   | Node Type   | images/sec |
| ------------------------| ----------- | ---------- |
| `imagenet-resnet-101`   | 1 * P40     | 47         |
| `imagenet-resnet-101`   | 4 * P40     | 181        |
| `imagenet-resnet-50`    | 4 * P40     | 288        |