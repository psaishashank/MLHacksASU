import requests
import json
import os
import openai
import spacy
import re
from spacy import displacy 
token = # Enter Assembly AI API token 


'''
This part of code uploads the file to a url
'''
filename = "audio.mp3"
def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

headers = {'authorization': token}
response = requests.post('https://api.assemblyai.com/v2/upload',
                        headers=headers,
                        data=read_file(filename))

print(response.json())
upload_url = response.json()['upload_url']




'''
This code sends to assemblyai for processing
'''
endpoint = "https://api.assemblyai.com/v2/transcript"
json = { "audio_url": upload_url,
        "auto_chapters": True,
        "sentiment_analysis": True,
            "punctuate": True,
    "format_text": True,
    "auto_highlights": True}
headers = {
    "authorization": token,
    "content-type": "application/json"
}
response = requests.post(endpoint, json=json, headers=headers)
print(response.json())



'''
Fetches Results from Assembly AI SERVERS
'''


endpoint = "https://api.assemblyai.com/v2/transcript/o4kxpz7x3w-2c9b-4977-bbbb-f9d99a1da00c/sentences"
headers = {
    "authorization": token,
}
masterData=[]
response = requests.get(endpoint, headers=headers)
#print(response.json())
data = response.json()
lst = data['sentences']
sentences=[]
# print(data)
# print(lst)
for index,i in enumerate(lst):
  subData ={}
  duration = i['end']-i['start']
  start = i['start']
  end = i['end']
  if index ==0:
    duration = (i['end']-0)
    start = 0
  subData['duration'] = duration/1000
  subData['start'] = start/1000
  subData['end'] = end/1000
  masterData.append(subData)
  # print(i['text'])
  sentences.append(i['text'])




'''
Using open AI to correct the grammar in order to identify the dialogues
'''


corrected=[]
openai.api_key = # OPEN AI key enter here
for i in sentences:

  response = openai.Completion.create(
    engine="text-davinci-002",
    prompt="Correct this to standard English:\n\n"+i,
    temperature=0,
    max_tokens=60,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0)
  corrected.append(response['choices'][0]['text'].strip('\n'))
print(corrected)


'''
Function that calculates the time stamp of dialogues
'''

def dialogueTimeStamp(word,indx):
  print('Index is',indx)
  tempLst= lst[indx]['words']
  print('WOrd is ',word)
  startTimeStamp = 0
  endTimeStamp =0
  occurence =0
  for dt in tempLst:
    if dt['text'] == word:
      occurence = occurence+1
      startTimeStamp = dt['start']
      endTimeStamp = dt['end']
  print(occurence)
  if occurence ==1:
    return startTimeStamp,endTimeStamp
  else:
    return 1e10 ,0



'''
Using NLP to identify subject , object , which are. useful for finding keywords for images
'''

# load english language model
nlp = spacy.load('en_core_web_sm',disable=['ner','textcat'])
stopwords = nlp.Defaults.stop_words

for i,data in zip(corrected,masterData):

  text = i#'To his surprise, a gentle voice responded, It is I, Maria, a calf who has found herself far from home'
  eTimeMax = 0
  sTimeMin = 1e10
  # create spacy 
  doc = nlp(text)
  data['sentence']=i
  bar = re.findall('"([^"]*)"', i)
  if len(bar)  != 0:
    data['dialogues'] = bar[0]
    my_string = bar[0].replace("'",'').replace('"','')

    for wrd in my_string.split():
      #print(wrd)
      sTime,eTime=dialogueTimeStamp(wrd,corrected.index(i))
      print('Wrd is ',wrd)
      print(sTime)
      print(eTime)
      print('***')
      if eTime> eTimeMax:
        eTimeMax= eTime
      if sTime < sTimeMin:
        sTimeMin= sTime
  else:
    data['dialogues']=None
    eTime = None
    sTime = None

  data['dialogueStartTime'] = sTimeMin/1000
  data['dialogueEndTime'] = eTimeMax/1000

  # displacy.render(doc, style='dep',jupyter=True)

  #print(i)
  keyWords = []
  for token in doc:
    if token.text.lower() not in stopwords:
        if (token.dep_=='nsubj' or token.dep_=='dobj' or token.dep_=='attr'):
          #print(token.text,token.dep_,token.pos_)
          keyWords.append(token.text+'.jpg')
  data['keyWords'] = keyWords

  #print('\n')



# Code to generate video
from moviepy.editor import *
import os

ni =0
clips = []

for index,scene in enumerate(masterData):

  clip = ImageSequenceClip(scene['keyWords'], fps = len(scene['keyWords'])/scene['duration'])
  ni = ni + len(scene['keyWords'])

     # use set_audio method from image clip to combine the audio with the image
  video_clip = clip.set_audio(None)
    # specify the duration of the new clip to be the duration of the audio clip
  video_clip.duration = scene["duration"]
    # set the FPS to 1
  video_clip.fps = len(scene['keyWords'])/scene['duration']
    # write the resuling video clip
  video_clip.write_videofile('v'+str(index)+'.mp4')

  clips.append(VideoFileClip('v'+str(index)+'.mp4'))



video = concatenate_videoclips( clips,method='compose')

audioclip = AudioFileClip("audio.mp3") 
video.duration = audioclip.duration

videoclip = video.set_audio(audioclip)
videoclip.write_videofile('output23.mp4',codec='mpeg4', fps=ni/audioclip.duration,audio=True)
