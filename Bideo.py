#!/usr/bin/env python
#-*- coding:utf-8 -*-
import os
import sys
import json
import shutil
import subprocess

def get_video_list(cache_dir):
    videos = []
    items = os.listdir(cache_dir)
    for item in items:
        filepath = os.path.join(cache_dir, item)
        if os.path.isdir(filepath):
            videos.append(filepath)
    return videos

def get_video_title(video_dir):
    jsonfile = os.path.join(video_dir, 'videoInfo.json')
    with open(jsonfile, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data['tabName']
        
def fix_file_header(infile, outfile):
    data = b''
    with open(infile, 'rb') as f:
        data = f.read()
    with open(outfile, 'wb') as f:
        f.write(data[9:])
        
def get_playable_avfiles(video_dir):
    avfiles = []
    for filename in os.listdir(video_dir):
        _, ext = os.path.splitext(filename)
        if ext.lower() != '.m4s':
            continue
        filepath = os.path.join(video_dir, filename)
        avfiles.append((filepath, os.stat(filepath).st_size))
    
    audiofile = avfiles[0][0]
    videofile = avfiles[1][0]
    if avfiles[0][1] > avfiles[1][1]:
        audiofile, videofile = videofile, audiofile
        
    real_audio = os.path.join(video_dir, 'audio.m4s')
    fix_file_header(audiofile, real_audio)
    real_video = os.path.join(video_dir, 'video.m4s')
    fix_file_header(videofile, real_video)
    return real_audio, real_video
    
def combine_avfiles(ffmpeg, audio, video, outfile):
    cmdline = [ffmpeg, '-i', audio, '-i', video, '-c:v', 'copy', '-c:a', 'copy', outfile]
    p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _1, _2 = p.communicate()
    os.remove(audio)
    os.remove(video)

def extract_videos(ffmpeg, cache_dir):
    ffmpeg = os.path.abspath(ffmpeg)
    cache_dir = os.path.abspath(cache_dir)
    outdir = cache_dir + '_output'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    print('Final video files will be write to directory: %s' % outdir)
    
    videos = get_video_list(cache_dir)
    for i, video_dir in enumerate(videos):
        sys.stdout.write('[%02d/%02d] Processing %s' % (i + 1, len(videos), os.path.basename(video_dir)))
        audiofile, videofile = get_playable_avfiles(video_dir)
        final_name = get_video_title(video_dir) + '.mp4'
        sys.stdout.write(' -> %s\n' % final_name)
        outfile = os.path.join(video_dir, final_name)
        combine_avfiles(ffmpeg, audiofile, videofile, outfile)
        shutil.move(outfile, os.path.join(outdir, final_name))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: %s <ffmpeg path> <bilibili cache directory>\n' % os.path.basename(sys.argv[0]))
    else:
        extract_videos(sys.argv[1], sys.argv[2])