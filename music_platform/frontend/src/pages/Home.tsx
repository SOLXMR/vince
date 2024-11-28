import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  Grid,
  TextField,
  IconButton,
  Menu,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import {
  PlayArrow,
  MoreVert,
  CloudDownload,
  Delete,
} from '@mui/icons-material';
import axios from 'axios';

interface Song {
  id: number;
  title: string;
  artist: string;
  album: string;
  duration: number;
  cover_art: string;
  bitrate: number;
}

const Home: React.FC = () => {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedSong, setSelectedSong] = useState<Song | null>(null);

  useEffect(() => {
    fetchSongs();
  }, []);

  const fetchSongs = async () => {
    try {
      const response = await axios.get('/api/songs/list');
      setSongs(response.data.songs);
    } catch (error) {
      console.error('Error fetching songs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, song: Song) => {
    setAnchorEl(event.currentTarget);
    setSelectedSong(song);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedSong(null);
  };

  const handleDownload = async (format: 'mp3' | 'wav') => {
    if (!selectedSong) return;

    try {
      const response = await axios.get(
        `/api/songs/download/${selectedSong.id}?format=${format}`,
        {
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `${selectedSong.title}.${format}`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading song:', error);
    }

    handleMenuClose();
  };

  const handleDelete = async () => {
    if (!selectedSong) return;

    try {
      await axios.delete(`/api/songs/${selectedSong.id}`);
      fetchSongs();
    } catch (error) {
      console.error('Error deleting song:', error);
    }

    handleMenuClose();
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const filteredSongs = songs.filter(
    (song) =>
      song.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      song.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
      song.album.toLowerCase().includes(searchTerm.toLowerCase())
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
    <Box sx={{ p: 3 }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search songs..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
      />
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
                  <Box>
                    <Typography variant="h6" component="div">
                      {song.title}
                    </Typography>
                    <Typography
                      variant="subtitle1"
                      color="text.secondary"
                      component="div"
                    >
                      {song.artist}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {song.album} • {formatDuration(song.duration)}
                    </Typography>
                  </Box>
                  <IconButton
                    aria-label="more"
                    onClick={(e) => handleMenuOpen(e, song)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
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
    </Box>
  );
};

export default Home; 