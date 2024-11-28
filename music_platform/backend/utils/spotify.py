import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import re

class SpotifyDownloader:
    def __init__(self, client_id, client_secret):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

    def get_track_info(self, spotify_url):
        # Extract track ID from URL
        track_id = spotify_url.split('/')[-1].split('?')[0]
        
        # Get track information
        track = self.spotify.track(track_id)
        
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration': int(track['duration_ms'] / 1000),  # Convert to seconds
            'cover_art': track['album']['images'][0]['url'] if track['album']['images'] else None
        }

    def search_youtube(self, title, artist):
        query = f"ytsearch:{title} {artist} official audio"
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                result = ydl.extract_info(query, download=False)
                if 'entries' in result and result['entries']:
                    return result['entries'][0]['webpage_url']
            except:
                return None
        return None

    def download_track(self, spotify_url, output_dir):
        try:
            # Get track info from Spotify
            track_info = self.get_track_info(spotify_url)
            
            # Search for the track on YouTube
            youtube_url = self.search_youtube(track_info['title'], track_info['artist'])
            
            if not youtube_url:
                raise Exception("Could not find track on YouTube")

            # Create a safe filename
            safe_filename = re.sub(r'[^\w\s-]', '', f"{track_info['artist']} - {track_info['title']}")
            safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
            
            # Set output template
            output_template = os.path.join(output_dir, f"{safe_filename}.%(ext)s")
            ydl_opts = {
                **self.ydl_opts,
                'outtmpl': output_template
            }

            # Download and convert the track
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            # Get the output filename
            output_filename = f"{safe_filename}.mp3"
            
            return {
                **track_info,
                'file_path': output_filename
            }

        except Exception as e:
            raise Exception(f"Failed to download track: {str(e)}")

# Example usage:
# downloader = SpotifyDownloader(client_id='your_client_id', client_secret='your_client_secret')
# track_info = downloader.download_track('spotify_track_url', 'output_directory') 