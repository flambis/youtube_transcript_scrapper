import argparse
import os
import scrapetube
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript
)
from youtube_transcript_api.formatters import TextFormatter
from yt_dlp import YoutubeDL
import sys
import concurrent.futures
import threading

# Création d'un verrou pour synchroniser l'accès au fichier de transcription
file_lock = threading.Lock()

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
        help="Chemin du dossier où sauvegarder les fichiers de transcription (par défaut: './transcriptions')."
    )
    parser.add_argument(
        '--file_name',
        default="transcriptions_channel",
        help="Nom du fichier txt à sauvegarder (sans extension, par défaut: 'transcriptions_channel')."
    )
    parser.add_argument(
        '--language',
        default='en',
        help="Langue de la transcription (par défaut: 'en')."
    )
    parser.add_argument(
        '--max_videos',
        type=int,
        default=None,
        help="Nombre maximum de vidéos à traiter. Si non spécifié, toutes les vidéos seront traitées."
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help="Nombre de threads à utiliser pour le traitement parallèle (par défaut: 5)."
    )
    return parser.parse_args()

def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Dossier créé: {folder_path}")
    else:
        print(f"Dossier existant: {folder_path}")

def fetch_videos(channel_id):
    print(f"Récupération des vidéos pour la chaîne ID: {channel_id}")
    try:
        return list(scrapetube.get_channel(channel_id))
    except Exception as e:
        print(f"Erreur lors de la récupération des vidéos: {e}")
        sys.exit(1)

def save_transcript(folder_path, file_name, transcript_text):
    file_path = os.path.join(folder_path, f"{file_name}.txt")
    with file_lock:  # Utilisation du verrou pour synchroniser l'accès au fichier
        with open(file_path, 'a', encoding='utf-8') as txt_file:
            txt_file.write(transcript_text + "\n")
    print(f"Transcription sauvegardée dans {file_path}")

def download_auto_subtitles(video_id, language='en', output_path='.'):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [language],
        'skip_download': True,
        'outtmpl': os.path.join(output_path, f'{video_id}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([video_url])
            subtitle_file = os.path.join(output_path, f'{video_id}.{language}.vtt')
            if os.path.exists(subtitle_file):
                # Convertir le fichier VTT en texte brut
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                transcript_text = ""
                for line in lines:
                    if not line.strip().isdigit() and not '-->' in line and line.strip():
                        transcript_text += line.strip() + " "
                save_transcript(output_path, "transcriptions_channel", transcript_text)
                print("Succès avec sous-titres générés automatiquement!")
                # Supprimer le fichier VTT après extraction
                os.remove(subtitle_file)
                return True
            else:
                print(f"Aucun sous-titre généré automatiquement disponible pour la vidéo {video_id}.")
                return False
        except Exception as e:
            print(f"Échec du téléchargement des sous-titres pour la vidéo {video_id}. Erreur: {e}")
            return False

def process_video(video, language, folder_path, file_name):
    video_id = video.get('videoId')
    if not video_id:
        print(f"ID vidéo non trouvé, passage à la suivante.")
        return False

    print(f"Traitement de la vidéo ID: {video_id}")
    try:
        # Tenter de récupérer les sous-titres manuels dans la langue spécifiée
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        formatter = TextFormatter()
        txt_formatted = formatter.format_transcript(transcript)
        save_transcript(folder_path, file_name, txt_formatted)
        print("Succès avec sous-titres manuels!")
        return True
    except (TranscriptsDisabled, NoTranscriptFound):
        # Tenter de récupérer les sous-titres générés automatiquement dans la même langue
        try:
            print(f"Transcription manuelle non trouvée pour la vidéo {video_id}, tentative avec les sous-titres générés automatiquement en '{language}'.")
            auto_success = download_auto_subtitles(video_id, language=language, output_path=folder_path)
            return auto_success
        except Exception as e:
            error_message = str(e).split('\n')[0]
            print(f"Erreur inattendue pour la vidéo {video_id}. Erreur: {error_message}")
            return False
    except Exception as e:
        error_message = str(e).split('\n')[0]
        print(f"Erreur inattendue pour la vidéo {video_id}. Erreur: {error_message}")
        return False

def process_videos_concurrently(videos, language, folder_path, file_name, max_videos, workers):
    total_videos = len(videos) if max_videos is None else min(len(videos), max_videos)
    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Limiter le nombre de vidéos si max_videos est spécifié
        videos_to_process = videos[:max_videos] if max_videos else videos

        # Préparer les tâches
        future_to_video = {
            executor.submit(process_video, video, language, folder_path, file_name): video
            for video in videos_to_process
        }

        for future in concurrent.futures.as_completed(future_to_video):
            video = future_to_video[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                video_id = video.get('videoId', 'Unknown')
                print(f"Erreur inattendue pour la vidéo {video_id}. Erreur: {e}")
                fail_count += 1

    print(f"\nTraitement terminé: {success_count} succès, {fail_count} échecs.")

def main():
    args = parse_arguments()
    # Demander channel_id si non fourni
    if not args.channel_id:
        args.channel_id = input("Entrez l'ID de la chaîne YouTube: ").strip()
        if not args.channel_id:
            print("L'ID de la chaîne est requis. Le script va s'arrêter.")
            sys.exit(1)
    ensure_folder_exists(args.folder_path)
    videos = fetch_videos(args.channel_id)
    if not videos:
        print("Aucune vidéo trouvée sur cette chaîne.")
        sys.exit(0)
    process_videos_concurrently(
        videos,
        args.language,
        args.folder_path,
        args.file_name,
        args.max_videos,
        args.workers
    )

if __name__ == "__main__":
    main()
