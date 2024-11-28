import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import re
import logging

logger = logging.getLogger(__name__)

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
        logger.debug(f"Extracted track ID: {track_id}")
        
        # Get track information
        track = self.spotify.track(track_id)
        logger.debug(f"Got track info from Spotify: {track['name']} by {track['artists'][0]['name']}")
        
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration': int(track['duration_ms'] / 1000),  # Convert to seconds
            'cover_art': track['album']['images'][0]['url'] if track['album']['images'] else None
        }

    def search_youtube(self, title, artist):
        query = f"ytsearch:{title} {artist} official audio"
        logger.debug(f"Searching YouTube with query: {query}")
        
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                result = ydl.extract_info(query, download=False)
                if 'entries' in result and result['entries']:
                    url = result['entries'][0]['webpage_url']
                    logger.debug(f"Found YouTube URL: {url}")
                    return url
                else:
                    logger.error("No results found on YouTube")
            except Exception as e:
                logger.error(f"Error searching YouTube: {str(e)}")
                return None
        return None

    def download_track(self, spotify_url, output_dir):
        try:
            # Get track info from Spotify
            logger.debug(f"Getting track info for URL: {spotify_url}")
            track_info = self.get_track_info(spotify_url)
            
            # Search for the track on YouTube
            logger.debug(f"Searching for track on YouTube: {track_info['title']} by {track_info['artist']}")
            youtube_url = self.search_youtube(track_info['title'], track_info['artist'])
            
            if not youtube_url:
                raise Exception("Could not find track on YouTube")

            # Create a safe filename
            safe_filename = re.sub(r'[^\w\s-]', '', f"{track_info['artist']}_-_{track_info['title']}")
            safe_filename = re.sub(r'[\s-]+', '_', safe_filename)
            logger.debug(f"Created safe filename: {safe_filename}")
            
            # Set output template
            output_template = os.path.join(output_dir, f"{safe_filename}.%(ext)s")
            logger.debug(f"Output template: {output_template}")
            
            ydl_opts = {
                **self.ydl_opts,
                'outtmpl': output_template
            }

            # Download and convert the track
            logger.debug(f"Downloading from YouTube URL: {youtube_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            # Get the output filename
            output_filename = f"{safe_filename}.mp3"
            logger.debug(f"Final output filename: {output_filename}")
            
            return {
                **track_info,
                'file_path': output_filename
            }

        except Exception as e:
            logger.error(f"Failed to download track: {str(e)}")
            raise Exception(f"Failed to download track: {str(e)}")

# Example usage:
# downloader = SpotifyDownloader(client_id='your_client_id', client_secret='your_client_secret')
# track_info = downloader.download_track('spotify_track_url', 'output_directory') 