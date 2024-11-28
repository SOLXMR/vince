import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Grid,
  TextField,
  IconButton,
  Menu,
  MenuItem,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  MoreVert,
  CloudDownload,
  Delete,
  PlayArrow,
  Pause,
  Add as AddIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import MusicPlayer from '../components/MusicPlayer';
import Upload from '../components/Upload';

const Home = () => {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedSong, setSelectedSong] = useState(null);
  const [playingSong, setPlayingSong] = useState(null);
  const [audioElement, setAudioElement] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSongs();
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
      }
    };
  }, []);

  const fetchSongs = async () => {
    try {
      setError(null);
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.get('/api/songs/list', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data?.songs) {
        setSongs(response.data.songs);
      } else {
        setError('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching songs:', error);
      setError(error.response?.data?.message || 'Failed to fetch songs');
      if (error.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = async (song) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      if (playingSong?.id === song.id) {
        if (audioElement.paused) {
          await audioElement.play();
          setIsPlaying(true);
        } else {
          audioElement.pause();
          setIsPlaying(false);
        }
        return;
      }

      // Stop current audio if any
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
      }

      // Create blob URL with authenticated request
      const response = await axios({
        method: 'GET',
        url: `http://localhost:5000/api/songs/stream/${song.file_path}`,
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(blob);

      // Create new audio element
      const audio = new Audio(audioUrl);
      
      // Add event listeners
      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        setError('Error playing audio');
        URL.revokeObjectURL(audioUrl);
      });

      // Play the audio
      await audio.play();
      setAudioElement(audio);
      setPlayingSong(song);
      setIsPlaying(true);

    } catch (error) {
      console.error('Error playing song:', error);
      setError('Failed to play song. Please try again.');
    }
  };

  const handleMenuOpen = (event, song) => {
    setAnchorEl(event.currentTarget);
    setSelectedSong(song);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedSong(null);
  };

  const handleDownload = async (format) => {
    if (!selectedSong) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios({
        method: 'GET',
        url: `http://localhost:5000/api/songs/stream/${selectedSong.file_path}?format=${format}`,
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob',
        withCredentials: true,
        maxRedirects: 0
      });

      const contentType = format === 'wav' ? 'audio/wav' : 'audio/mpeg';
      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const baseFilename = selectedSong.file_path.split('.')[0];
      link.setAttribute('download', `${baseFilename}.${format}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading song:', error);
      setError('Failed to download song. Please try again.');
    }

    handleMenuClose();
  };

  const handleDelete = async () => {
    if (!selectedSong) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      await axios.delete(`/api/songs/${selectedSong.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (playingSong?.id === selectedSong.id) {
        if (audioElement) {
          audioElement.pause();
          audioElement.src = '';
        }
        setPlayingSong(null);
        setIsPlaying(false);
      }

      await fetchSongs();
    } catch (error) {
      console.error('Error deleting song:', error);
      if (error.response?.status === 401) {
        navigate('/login');
      }
    }

    handleMenuClose();
  };

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const filteredSongs = songs.filter(
    (song) =>
      song.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      song.artist?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      song.album?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, pb: 10 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {showUpload ? (
        <>
          <Button
            variant="outlined"
            onClick={() => setShowUpload(false)}
            sx={{ mb: 3 }}
          >
            Back to Songs
          </Button>
          <Upload onUploadSuccess={() => {
            setShowUpload(false);
            fetchSongs();
          }} />
        </>
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search songs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowUpload(true)}
            >
              Upload
            </Button>
          </Box>

          {filteredSongs.length === 0 ? (
            <Typography variant="h6" textAlign="center" color="text.secondary">
              No songs found
            </Typography>
          ) : (
            <Grid container spacing={3}>
              {filteredSongs.map((song) => (
                <Grid item xs={12} sm={6} md={4} key={song.id}>
                  <Card>
                    <CardMedia
                      component="img"
                      height="140"
                      image={song.cover_art || '/default-album-art.jpg'}
                      alt={song.title}
                    />
                    <CardContent>
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                        }}
                      >
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" component="div">
                            {song.title}
                          </Typography>
                          <Typography
                            variant="subtitle1"
                            color="text.secondary"
                            component="div"
                          >
                            {song.artist || 'Unknown Artist'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {song.album || 'Unknown Album'} • {formatDuration(song.duration || 0)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <IconButton
                            onClick={() => handlePlayPause(song)}
                            color={playingSong?.id === song.id ? "primary" : "default"}
                          >
                            {playingSong?.id === song.id && isPlaying ? (
                              <Pause />
                            ) : (
                              <PlayArrow />
                            )}
                          </IconButton>
                          <IconButton
                            aria-label="more"
                            onClick={(e) => handleMenuOpen(e, song)}
                          >
                            <MoreVert />
                          </IconButton>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleDownload('wav')}>
          <CloudDownload sx={{ mr: 1 }} /> Download WAV
        </MenuItem>
        <MenuItem onClick={() => handleDownload('mp3')}>
          <CloudDownload sx={{ mr: 1 }} /> Download MP3
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <Delete sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>

      <MusicPlayer
        currentSong={playingSong}
        audioElement={audioElement}
        onPlayPause={() => playingSong && handlePlayPause(playingSong)}
        isPlaying={isPlaying}
      />
    </Box>
  );
};

export default Home; 