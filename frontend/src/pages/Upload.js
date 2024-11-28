import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import { CloudUpload, Link as LinkIcon } from '@mui/icons-material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Upload = () => {
  const [uploadType, setUploadType] = useState(0); // 0 for file, 1 for Spotify
  const [file, setFile] = useState(null);
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [album, setAlbum] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleTabChange = (event, newValue) => {
    setUploadType(newValue);
    setError('');
  };

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.type.includes('audio/mpeg')) {
        setError('Please select an MP3 file');
        return;
      }
      setFile(selectedFile);
      setError('');
      
      // Try to extract title and artist from filename
      const filename = selectedFile.name.replace('.mp3', '');
      const parts = filename.split(' - ');
      if (parts.length === 2) {
        setArtist(parts[0].trim());
        setTitle(parts[1].trim());
      } else {
        setTitle(filename);
      }
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('artist', artist);
    formData.append('album', album);

    try {
      await axios.post('/api/songs/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });
      navigate('/');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.message || err.message || 'Failed to upload song');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleSpotifyUpload = async (e) => {
    e.preventDefault();
    if (!spotifyUrl) {
      setError('Please enter a Spotify URL');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const response = await axios.post('/api/songs/upload/spotify', { url: spotifyUrl });
      console.log('Spotify upload response:', response.data);
      navigate('/');
    } catch (err) {
      console.error('Spotify upload error:', err);
      setError(err.response?.data?.message || err.message || 'Failed to process Spotify URL');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
        <Typography variant="h5" gutterBottom align="center">
          Upload Music
        </Typography>
        
        <Tabs
          value={uploadType}
          onChange={handleTabChange}
          centered
          sx={{ mb: 3 }}
        >
          <Tab label="File Upload" icon={<CloudUpload />} />
          <Tab label="Spotify Link" icon={<LinkIcon />} />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {uploadType === 0 ? (
          // File Upload Form
          <Box component="form" onSubmit={handleFileUpload}>
            <input
              type="file"
              accept=".mp3"
              style={{ display: 'none' }}
              ref={fileInputRef}
              onChange={handleFileSelect}
            />
            <Button
              variant="outlined"
              startIcon={<CloudUpload />}
              onClick={() => fileInputRef.current?.click()}
              fullWidth
              sx={{ mb: 3 }}
            >
              {file ? file.name : 'Select MP3 File'}
            </Button>
            <TextField
              fullWidth
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Artist"
              value={artist}
              onChange={(e) => setArtist(e.target.value)}
              required
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Album"
              value={album}
              onChange={(e) => setAlbum(e.target.value)}
              sx={{ mb: 3 }}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={uploading || !file}
            >
              {uploading ? (
                <>
                  <CircularProgress size={24} sx={{ mr: 1 }} />
                  {progress > 0 && `${progress}%`}
                </>
              ) : (
                'Upload Song'
              )}
            </Button>
          </Box>
        ) : (
          // Spotify Link Form
          <Box component="form" onSubmit={handleSpotifyUpload}>
            <TextField
              fullWidth
              label="Spotify URL"
              placeholder="https://open.spotify.com/track/..."
              value={spotifyUrl}
              onChange={(e) => setSpotifyUrl(e.target.value)}
              required
              sx={{ mb: 3 }}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={uploading || !spotifyUrl}
            >
              {uploading ? (
                <CircularProgress size={24} sx={{ mr: 1 }} />
              ) : (
                'Download from Spotify'
              )}
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Upload; 