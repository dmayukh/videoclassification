"""
   Author: Mayukh Dutta
"""
import os
import os.path
import numpy as np
from PIL import Image
import torch
import matplotlib.pyplot as plt
import youtube_dl

yl = youtube_dl.YoutubeDL({'format': 'best'})

def getproperties(url):
    m3u8, width, height, fps = None, None, None, None
    try:
        quality = yl.extract_info(url, download=False)
        m3u8 = quality['url']
        width = quality['width']
        height = quality['height']
        fps = quality['fps']
    except Exception as e:
        print("Error downloading the metadata for the video url {}, error {}".format(url, e.__class__))
        raise Exception("Metadata fetch error")
    return m3u8, width, height, fps


import re
""" Get the size of the video frames from the metadata of the downloaded stream
    This has been tested to work with the metadata from the youtube video streams only
"""
def getsize(prop):
    """
    Args:
        a byte array
    Returns:
        (int, int): width and height of the video frames
    """
    grp = None
    width = None
    height = None
    #get the part of the bytes after rgb24
    p = re.compile(rb'rgb24\s*(.*)')
    try:
        m = p.search(prop)
        if m:
            grp = m.group(1)
        p = re.compile(rb'((\d+)(\s|x|\.)(\d+))')
        m = p.search(grp)
        try:
            if m:
                width = int(m.group(2))
                height = int(m.group(4))
        except:
            print("Error when extracting the size from the downloaded video stream!")
    except:
        print("Error parsing the properties of the downloaded video")
        raise Exception("Get size error")
    return width, height

import ffmpeg
"""
    Download the video using the video stream link, fps and a provided width for scaling the frames
"""
def downloadvideo(m3u8, fps, startsecs, durationsecs, width=360):
    try:
        out, prop = (
                ffmpeg
                .input(m3u8, ss=startsecs, t=durationsecs) #use this instead of trim
                #.trim(start_frame=stfr, end_frame=enfr) #buggy, does not work!
                .filter('fps', fps=fps, round='up')
                .filter('scale', 360, -1)
                .output('pipe:', format='rawvideo', pix_fmt='rgb24')
                .run(capture_stdout=True, quiet = True))
    except Exception as e:
        print("Error reading the video stream, error was {}".format(e.__class__))
        raise Exception("Download error")
    return out, prop

def getvideo(out, width, height):
    try:
        video = (np.frombuffer(out, np.uint8).reshape([-1, width, height, 3]))  
    except:
        print("Error reshaping video byte array to numpy array")
        raise Exception("Fetch video error")
    return video

import imageio
import os
import traceback
import sys
"""
    Parse all videos in the video_list and generate image files for training
"""
def parsevideos(video_list, clip_len=None, save_images=True, save_videos=False, rootpath=None, videopath=None):
    """
        Arg: video_list is a dictionary of url (a youtube video link) and the category: string
             Optional: clip_len: int, length of the clip in seconds, default = 30
                       save_images: save the images from the frames to directory named after the category, default = True
                       save_videos: save the videos to a directory in videopath, default = False
                       rootpath: the directory for the training images
                       videopath: the directory for the extracted videos
    """
    annotationsfile = "annotations.txt"
    clsses = {}
    free_ids = 0
    defaultcliplen = 30 #seconds
    if clip_len is not None:
        cliplen = int(clip_len)
    else:
        cliplen = defaultcliplen
    if rootpath is None:
        raise ValueError("rootpath must be provided.")
    vid_idx = 0
    #clean up old annotations file
    annotationsfilepath = rootpath + "/" + annotationsfile
    try:
        os.remove(annotationsfilepath)
    except:
        print("Error removing the annotations file {}".format(annotationsfilepath))
    for vl in video_list:
        try:
            #get the metadata for the video
            if 'url' in vl:
                url = vl['url']
            else:
                raise Exception("No video url provided, skipping...")
            m3u8, width, height, fps = getproperties(url)
            #get the start and end frame requirements for the video, if provided 
            if 'start' in vl:
                start = int(vl['start'])
            else: 
                start = 0
            if 'end' in vl:
                end = int(vl['end'])
            else:
                end = cliplen
            #get the category of the video
            if 'category' in vl:
                category = vl['category']
            else:
                raise Exception("No category specified for the video {}".format(url))
            #get the class id for the category
            if category not in clsses:
                clsses[category] = free_ids
                free_ids += 1
            class_id = clsses[category]
            print("Class id is {}".format(class_id))
            print("Downloading from {} to {} of length {}".format(start, end, end-start))
            out, prop = downloadvideo(m3u8, fps, start, end - start, width/2)
            width, height = getsize(prop)
            #the numpy array of the video
            video = getvideo(out, height, width)
            if videopath is not None:
                pathtovideo = os.path.join(videopath + "/" + category)
                if not os.path.exists(pathtovideo):
                    os.makedirs(pathtovideo)
                fullpath = pathtovideo + "/" + "video{}.mp4".format(vid_idx)
                print("Saving video to {}".format(fullpath))
                imageio.mimwrite(fullpath, video , fps = fps)
            if rootpath is not None:
                #create a folder to save the images from the video, some arbritrary naming
                #we will use the index of the video
                pathtoimages = os.path.join(rootpath + "/" + category + "/" + str(vid_idx))
                if not os.path.exists(pathtoimages):
                    os.makedirs(pathtoimages)
                for idx in range(video.shape[0]):
                    fullpath = pathtoimages + "/" + "img_{}.jpg".format(idx)
                    im = Image.fromarray(video[idx])
                    im.save(fullpath)
                frame_cnt = video.shape[0]
                print("Saved {} images in {}".format(frame_cnt, pathtoimages))
                #write the image paths to the annotations file, path, start frame, end frame, class id
                with open(annotationsfilepath, 'a') as filetowrite:
                    filetowrite.write("{}/{} {} {} {}\n".format(category, vid_idx, 0, frame_cnt, class_id))
                
            vid_idx += 1
        except Exception as e:
            print(e)
            traceback.print_exception(*sys.exc_info())
            print("Error in processing the video at {}".format(vl['url']))
            continue
