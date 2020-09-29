<p align="center">
  <a href="https://github.com/dome272/Instagram-DeepFake-Bot">
    <img src="files/logo.png" alt="Logo" width="80" height="80">
  </a>
</p>

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Issues][issues-shield]][issues-url]
# Instagram-DeepFake-Bot
An Instagram Bot serving as an account, people can use to create DeepFakes on Instagram.

The DeepFakes are created using [First Order Model for Image Animation](https://github.com/AliaksandrSiarohin/first-order-model) and the Faces are cropped using [Ultra-Light-Fast-Generic-Face-Detector](https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB)

# Explain Video:
[![DeepFake Video on Youtube](https://i.imgur.com/JvnD4XC.png)](https://www.youtube.com/watch?v=qKWYGH8iSng)

# Disclaimer:
The code needed a lot of configuring in order to work in my specific workplaces. 
I tried making it as easy as possible to run it yourself. Errors may occur!
(Also this code only serves as a "show - off" and is not intended to be run since Instagram's terms of services strictly prohibits this.)
Run it at your own risk.


## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites & Installation

* Code was written and tested in Python 3.6.5 and 3.6.10
* Install the requirements.txt
```pip install -r requirements.txt```
* Install autocrop
```pip install autocrop```
  * locate autocrop (/usr/local/lib/python3.6/dist-packages/autocrop)
  * replace entire folder with [my updated autocrop](https://github.com/dome272/Instagram-DeepFake-Bot/blob/face_detection/autocrop)
* deepfake.py requires numpy=1.15 -> we need a feature from numpy=1.16
  * locate numpy-core (/usr/local/lib/python3.6/dist-packages/numpy/core)
  * replace function_base.py with [my updated numpy function_base.py](https://github.com/dome272/Instagram-DeepFake-Bot/blob/files/function_base.py)
* Additional things:
  * ffmpeg
  * cuda
  * opencv (I had to recompile it on Ubuntu 18.04.4) -> [Install Opencv](https://docs.opencv.org/master/d7/d9f/tutorial_linux_install.html) and follow [this guide](https://github.com/opencv/opencv/issues/8471#issuecomment-321199220)
  * GPU (I used a GTX 1080 renting on [vast.ai](https://vast.ai/console/create/))
  

### Running it

1. Edit [main.py](https://github.com/dome272/Instagram-DeepFake-Bot/blob/master/main.py) on line 596 with your account details.
2. ```python3.6 main.py```
3. Wait for the Instagram-Login to happen.
4. Wait for Checker-,Editor-,and Sender-Class to be initialised.


### Adding ranks to users
1. Go to [other_tools](https://github.com/dome272/Instagram-DeepFake-Bot/blob/other_tools)
2. Run ```python3.6 add_donator username rank```
  * Rank 1: 30 seconds videos + priority queue
  * Rank 2: 45 seconds videos + priority queue + watermark removal
  * Rank 3: 60 seconds videos + priority queue + watermark removal
  * (Every other user is initially Rank 0)

### Checking stats
* all stats can be found in log.json

<!-- CONTACT -->
## Contact
Instagram [@dome271](https://instagram.com/dome271) 
Email: d6582533@gmail.com


<!-- MARKDOWN LINKS & IMAGES -->
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=flat-square
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/dominic-rampas-7bb2ba1b8/
