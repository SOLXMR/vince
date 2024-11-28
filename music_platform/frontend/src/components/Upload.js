import React, { useState } from 'react';
import axios from 'axios';
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
  IconButton,
  InputAdornment,
} from '@mui/material';
import { CloudUpload, Link as LinkIcon, Clear } from '@mui/icons-material';

const Upload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadType, setUploadType] = useState(0); // 0 for file, 1 for Spotify
  const [spotifyUrl, setSpotifyUrl] = useState('');

  const handleTabChange = (event, newValue) => {
    setUploadType(newValue);
    setError('');
    setSuccess('');
    setFile(null);
    setTitle('');
    setSpotifyUrl('');
  };

  const validateSpotifyUrl = (url) => {
    return url.includes('spotify.com/track/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (uploadType === 0) {
      // File upload
      if (!file) {
        setError('Please select a file');
        return;
      }
    } else {
      // Spotify link
      if (!spotifyUrl) {
        setError('Please enter a Spotify link');
        return;
      }
      if (!validateSpotifyUrl(spotifyUrl)) {
        setError('Please enter a valid Spotify track URL');
        return;
      }
    }

    try {
      setLoading(true);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      let response;
      if (uploadType === 0) {
        // File upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', title || file.name);

        response = await axios.post('http://localhost:5000/api/songs/upload', formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      } else {
        // Spotify link upload
        response = await axios.post('http://localhost:5000/api/songs/upload/spotify', 
          { spotify_url: spotifyUrl },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
      }

      if (response.data.status === 'success') {
        setSuccess('Upload successful!');
        setFile(null);
        setTitle('');
        setSpotifyUrl('');
        if (uploadType === 0) {
          const fileInput = document.querySelector('input[type="file"]');
          if (fileInput) {
            fileInput.value = '';
          }
        }
        if (onUploadSuccess) {
          setTimeout(onUploadSuccess, 1500);
        }
      }
    } catch (error) {
      console.error('Upload error:', error.response?.data || error);
      setError(error.response?.data?.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!title) {
        const fileName = selectedFile.name.replace(/\.[^/.]+$/, '');
        setTitle(fileName);
      }
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4, p: 2 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Upload Song
        </Typography>

        <Tabs
          value={uploadType}
          onChange={handleTabChange}
          centered
          sx={{ mb: 3 }}
        >
          <Tab icon={<CloudUpload />} label="File Upload" />
          <Tab icon={<LinkIcon />} label="Spotify Link" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          {uploadType === 0 ? (
            // File Upload Form
            <>
              <Box sx={{ mb: 2 }}>
                <input
                  accept=".mp3,.wav,.ogg"
                  type="file"
                  onChange={handleFileChange}
                  style={{ display: 'block', width: '100%', marginBottom: '1rem' }}
                  id="song-file-input"
                />
                {file && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Selected file: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </Typography>
                )}
              </Box>

              <TextField
                fullWidth
                label="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                margin="normal"
                placeholder="Enter song title (optional)"
              />
            </>
          ) : (
            // Spotify Link Form
            <TextField
              fullWidth
              label="Spotify Track URL"
              value={spotifyUrl}
              onChange={(e) => setSpotifyUrl(e.target.value)}
              margin="normal"
              placeholder="https://open.spotify.com/track/..."
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LinkIcon />
                  </InputAdornment>
                ),
                endAdornment: spotifyUrl && (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setSpotifyUrl('')} edge="end">
                      <Clear />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          )}

          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            disabled={loading || (!file && !spotifyUrl)}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Upload; 