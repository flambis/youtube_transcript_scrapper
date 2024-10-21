import argparse
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import scrapetube

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Télécharge les transcriptions des vidéos d'une chaîne YouTube."
    )
    parser.add_argument(
        '--channel_id',
        help="ID de la chaîne YouTube."
    )
    parser.add_argument(
        '--folder_path',
        default="./transcriptions",
        help="Chemin du dossier où sauvegarder le fichier txt (par défaut: './transcriptions')."
    )
    parser.add_argument(
        '--file_name',
        default="transcriptions_channel",
        help="Nom du fichier txt à sauvegarder (sans extension, par défaut: 'transcriptions_channel')."
    )
    parser.add_argument(
        '--language',
        default='en',
        help="Langue de la transcription (par défaut: 'hi')."
    )
    args = parser.parse_args()

    # Demander channel_id si non fourni
    if not args.channel_id:
        args.channel_id = input("Entrez l'ID de la chaîne YouTube: ").strip()
        if not args.channel_id:
            print("L'ID de la chaîne est requis. Le script va s'arrêter.")
            exit(1)
    return args

def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Dossier créé: {folder_path}")
    else:
        print(f"Dossier existant: {folder_path}")

def fetch_videos(channel_id):
    print(f"Récupération des vidéos pour la chaîne ID: {channel_id}")
    try:
        return scrapetube.get_channel(channel_id)
    except Exception as e:
        print(f"Erreur lors de la récupération des vidéos: {e}")
        exit(1)

def save_transcript(folder_path, file_name, transcript_text):
    file_path = os.path.join(folder_path, f"{file_name}.txt")
    with open(file_path, 'a', encoding='utf-8') as txt_file:
        txt_file.write(transcript_text + "\n")
    print(f"Transcription sauvegardée dans {file_path}")

def process_videos(videos, language, folder_path, file_name):
    formatter = TextFormatter()
    total = len(videos)
    success_count = 0
    fail_count = 0

    for idx, video in enumerate(videos, start=1):
        video_id = video.get('videoId')
        if not video_id:
            print(f"[{idx}/{total}] ID vidéo non trouvé, passage à la suivante.")
            fail_count += 1
            continue
        print(f"[{idx}/{total}] Traitement de la vidéo ID: {video_id}")
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            txt_formatted = formatter.format_transcript(transcript)
            save_transcript(folder_path, file_name, txt_formatted)
            print("Succès!")
            success_count += 1
        except Exception as e:
            print(f"Transcription non trouvée pour la vidéo {video_id}. Erreur: {e}")
            fail_count += 1

    print(f"\nTraitement terminé: {success_count} succès, {fail_count} échecs.")

def main():
    args = parse_arguments()
    ensure_folder_exists(args.folder_path)
    videos = fetch_videos(args.channel_id)
    process_videos(videos, args.language, args.folder_path, args.file_name)

if __name__ == "__main__":
    main()
