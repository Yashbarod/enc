import os
import sys
import json
import time
import ffmpeg
from subprocess import call, check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

def get_codec(filepath, channel='v:0'):
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                            '-show_entries', 'stream=codec_name,codec_tag_string', '-of', 
                            'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

def encode(filepath):
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = f"{basefilepath} 10bit HEVC.mkv"
    assert(output_filepath != filepath)
    if os.path.isfile(output_filepath):
        print('Skipping "{}": file already exists'.format(output_filepath))
        return None
    print(filepath)
    # Get the video channel codec
    video_codec = get_codec(filepath, channel='v:0')
    if video_codec == []:
        print('Skipping: no video codec reported')
        return None
    # Video transcode options
    if video_codec[0] == 'hevc':
        if video_codec[1] == 'hvc1':
            print('Skipping: already h265 / hvc1')
            return None
        else:
            # Copy stream to hvc1
            video_opts = '-c:v copy -tag:v hvc1'
    else:
        # Transcode to h265 / hvc1
        video_opts = '-c:v libx265 -preset veryfast -cq 25 -qmin 25 -qmax 25 -b:v 0 -profile:v main10 -pix_fmt p010le -rc-lookahead 40 -no-scenecut 1 -init_qpP 23 -init_qpB 25 -init_qpI 21 -weighted_pred 1 -map 0:v -map_chapters 0 -c:s copy -map 0:s? -c:t copy -map 0:t?'
    # Get the audio channel codec
    audio_codec = get_codec(filepath, channel='a:0')
    if audio_codec == []:
        audio_opts = ''
    elif audio_codec[0] == 'libopus':
        audio_opts = '-ac 2 -c:a libopus -b:a 96k -map 0:a? -map_metadata 0'
    else:
        audio_opts = '-c:a libopus -b:a 96k -map 0:a? -map_metadata 0'
    call(['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath])
    
    return output_filepath

def get_thumbnail(in_filename, path, ttl):
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
      return None

def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0

def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
      return metadata.get("width"), metadata.get("height")
    else:
      return 1280, 720
