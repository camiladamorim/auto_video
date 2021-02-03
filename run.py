def auto_video(query,summary,path_to_audio):    

    # case in colab add:
    # !pip install setuptools cookiejar git+https://github.com/Joeclinton1/google-images-download.git dhash ffmpeg-python pydub

    import urllib3
    import requests 
    from bs4 import BeautifulSoup
    import numpy as np
    import os
    import ffmpeg
    import gdown
    import pandas as pd
    from os import listdir
    from PIL import Image
    from google_images_download import google_images_download 
    import dhash
    from scipy.spatial.distance import hamming
    import json
    import re
    import os
    import math
    import numpy as np
    from pydub import AudioSegment


    print("###### init ######")
    
    title=re.sub(' ','_',query)
    title=re.sub(',','_',title)
    title=re.sub('\.','',title)
    query=re.sub('_',' ',title)

    response = google_images_download.googleimagesdownload() 

    def downloadimages(query): 
        # aspect ratio = the height width ratio of images to download ("tall, square, wide, panoramic") 
        arguments = {"keywords": query, 
              "format": "jpg", 
              "limit":10,
              "print_urls":True, 
              "size": "medium", 
              "aspect_ratio":"panoramic"} 
        try: 
            response.download(arguments)  
        except FileNotFoundError: 
            arguments = {"keywords": query, 
                "format": "jpg", 
                "limit":4, 
                "print_urls":True, 
                "size": "medium"} 
            try: 
                response.download(arguments) 
            except: 
                pass

    print("###### downloading images ######")
    downloadimages(query) 

    print("###### hashing images ######")

    def hashing(image,size=(25,25)):
        img = Image.open(image).convert("L")
        img2 = img.resize(size)
        row, col = dhash.dhash_row_col(img2)
        hash=dhash.format_hex(row, col)
        return(hash)

    print("###### saving hashes ######")

    dir='./downloads/' + query + '/'
    dirs = listdir(dir)

    print("###### calculating differences between images ######")

    hashes=[]
    for i in dirs:
        a=dir+i
        hash=hashing(a)
        hashes.append(hash)

    def dif_hashing(a,b):
        diff=dhash.get_num_bits_different(int(a,16),int(b,16))
        return(diff)

    list_difs_hashings=[0]
    for i in range(len(hashes)):
        for j in range(len(hashes)):
            if i<j:
                diff_hash = dif_hashing(hashes[i],hashes[j])
                if list_difs_hashings[0]==0:
                    list_difs_hashings[0]=diff_hash
                elif list_difs_hashings[0]<diff_hash:
                    list_difs_hashings.append(diff_hash)
                    list_difs_hashings.sort()
                    list_difs_hashings=list_difs_hashings[-4:]
                    list_difs_hashings.sort(reverse=True)


    images=[]
    for i in range(len(hashes)):
        for j in range(len(hashes)):
            if i<j:
                diff_hash = dif_hashing(hashes[i],hashes[j])
                if diff_hash in list_difs_hashings:
                    if dirs[i] not in images:
                        images.append(dirs[i])
                    if dirs[j] not in images:
                        images.append(dirs[j])
                if len(images)>4:
                    images=images[:4]
                    break

    if len(images)!=4:
      return("try again, less than 4 images")

    print("###### creating folders and saving the most different ones ######")

    os.mkdir('./downloads/diffimages')
    os.mkdir('./downloads/movie')
    for image in images:
        im=Image.open('./downloads/' + query + '/'+image)
        im.save('./downloads/diffimages/' + image)

    print("###### making a video out of images ######")
    SECONDS_BY_IMG=6
    FRAMERATE=1/SECONDS_BY_IMG
    stream=ffmpeg.input('downloads/diffimages/'+'*.jpg', pattern_type='glob', framerate=FRAMERATE).output('downloads/movie/'+title+'.mp4').run()

    summary_list_parts = summary.split(".")
    list_absolute_subtitle_time_by_phrase=[]
    for phrase in summary_list_parts:
        list_absolute_subtitle_time_by_phrase.append(SECONDS_BY_IMG)

    endtime_for_each_sub = np.cumsum(list_absolute_subtitle_time_by_phrase)
    init_time_for_each_sub = endtime_for_each_sub-list_absolute_subtitle_time_by_phrase
    endtime_for_each_sub = endtime_for_each_sub.tolist()
 
    print(type(endtime_for_each_sub),type(endtime_for_each_sub[1]))
    print("###### create rst file from summary ######")
    subtitles_path='downloads/movie/subtitles_of_'
    f = open(subtitles_path + title + '.rst', "w")
    for i in range(len(summary_list_parts)):
        if endtime_for_each_sub[i] < 10:
            endtime_for_each_sub_ = "0"+str(endtime_for_each_sub[i])
        else:
            endtime_for_each_sub_ = str(endtime_for_each_sub[i])

        if init_time_for_each_sub[i] < 10:
            init_time_for_each_sub_ = "0"+str(init_time_for_each_sub.tolist()[i])
        else:
            init_time_for_each_sub_ = str(init_time_for_each_sub[i])
        
        f.write(str(i+1)+"\n00:00:"+init_time_for_each_sub_+",00 --> 00:00:"+endtime_for_each_sub_+",00\n"+summary_list_parts[i]+"\n")

    f.close()
    f = open(subtitles_path + title + '.rst', "r")
    print("###### setting environment variables ######")
    os.environ["VIDEO"] = './downloads/movie/'+title +'.mp4'
    os.environ["SUBTITLES"] = subtitles_path +title+'.rst'
    os.environ["VIDEO_WITH_SUBTITLES_AND_AUDIO"] = "./downloads/movie/subtitled_with_music_"+title +'.mp4'
    os.environ["VIDEO_WITH_SUBTITLES"] = "./downloads/movie/subtitled_"+title +'.mp4'
    os.environ["AUDIO"] = path_to_audio
    AUDIO = path_to_audio

    print("###### creating a video with subtitles ######")
    !ffmpeg -i $VIDEO -vf subtitles=$SUBTITLES $VIDEO_WITH_SUBTITLES


    sound = AudioSegment.from_mp3(path_to_audio)

    sound_trimmed = sound[:SECONDS_BY_IMG*4*1000]
    sound_trimmed.export(path_to_audio, format="mp3")
    print("############\n\n\n\n\n",len(sound_trimmed))
    print("###### merging audio in video ######")
    !ffmpeg -i $VIDEO_WITH_SUBTITLES -i $AUDIO -c:v libx264 -vf format=yuv420p $VIDEO_WITH_SUBTITLES_AND_AUDIO




#from google.colab import drive 
# drive.mount('/content/gdrive')

# query = "Lifestyle choices can reduce risk for heartburn, study finds."
# summary = "Women who make healthy lifestyle choices can significantly reduce the risk of heartburn. Other thing. ooooother thing. one more thing"
# path_to_audio= 'gdrive/MyDrive/path/to/audio/audio.mp3'
# auto_video(query,summary,path_to_audio)