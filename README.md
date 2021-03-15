# Video Classification

Created a small kinetics train, valid and test json to try out the downloads

Use the .json files here in this repo to replace the json files in the resources folder when you checkout the kinetics-downloader https://github.com/Showmax/kinetics-downloader.git

The training takes too long, even for a dataset as small as 10 images.

I have a custom video to training frames converter, the training data is generated as per the specifications here https://video-dataset-loading-pytorch.readthedocs.io/en/latest/

The train.py in torch object detection does not seem to work with the videos saved using my custom downloader, it works with the ones downloaded using the kinetics-downloader yhough

Use the training code from here https://github.com/pytorch/vision/blob/master/references/video_classification/train.py


Check the cloab notebook for the test runs https://colab.research.google.com/drive/1932J5AKnf6RHSCyQg0H1Jqr7s3rowSmZ?usp=sharing


