from youtube_transcript_api import YouTubeTranscriptApi                            # Install youtube_transcript_api and scrapetube
from youtube_transcript_api.formatters import Formatter
from youtube_transcript_api.formatters import TextFormatter
import scrapetube

#Enter the Youtube Channel ID
channel_id = '' 

#Enter the path of the folder to save the txt file
folder_path = '' 

#Enter the name of the txt file to be saved
file_name = ''
                                                            
videos = scrapetube.get_channel(channel_id)

for video in videos:
    video_id = video['videoId']
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi']) #Enter the language of the transcript
        formatter = TextFormatter()
        txt_formatted = formatter.format_transcript(transcript)
        with open(f'{folder_path}/{file_name}.txt', 'a', encoding='utf-8') as txt_file:
            txt_file.write(txt_formatted)
        print('success!')
    except:
        print('subtitles not found!')

