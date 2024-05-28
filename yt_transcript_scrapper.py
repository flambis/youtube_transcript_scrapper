from youtube_transcript_api import YouTubeTranscriptApi                            # Install youtube_transcript_api and scrapetube
from youtube_transcript_api.formatters import Formatter
from youtube_transcript_api.formatters import TextFormatter
import scrapetube

channel_id = 'UCBIT1FSJW6yTlzqK-31FDWg'                                             #Enter the Youtube Channel ID
folder_path = '/home/llmhindi/Laksh/Corpus/Youtube_transcript'                      #Enter the path of the folder to save the txt file
file_name = 'LIV Comedy'                                                            #Enter the name of the txt file to be saved
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

