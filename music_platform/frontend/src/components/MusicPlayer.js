import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  IconButton,
  Slider,
  Typography,
  Paper,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  VolumeOff,
} from '@mui/icons-material';

const MusicPlayer = ({ currentSong, audioElement, onPlayPause, isPlaying }) => {
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const progressRef = useRef(null);

  useEffect(() => {
    if (audioElement) {
      // Set initial volume
      audioElement.volume = volume;

      // Add event listeners
      const handleTimeUpdate = () => {
        if (!isDragging) {
          setProgress(audioElement.currentTime);
        }
      };

      const handleLoadedMetadata = () => {
        setDuration(audioElement.duration);
        setProgress(0);
      };

      const handleEnded = () => {
        setProgress(0);
      };

      audioElement.addEventListener('timeupdate', handleTimeUpdate);
      audioElement.addEventListener('loadedmetadata', handleLoadedMetadata);
      audioElement.addEventListener('ended', handleEnded);

      return () => {
        audioElement.removeEventListener('timeupdate', handleTimeUpdate);
        audioElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audioElement.removeEventListener('ended', handleEnded);
      };
    }
  }, [audioElement, volume, isDragging]);

  const handleVolumeChange = (event, newValue) => {
    const volumeValue = newValue / 100;
    setVolume(volumeValue);
    if (audioElement) {
      audioElement.volume = volumeValue;
    }
    if (volumeValue === 0) {
      setIsMuted(true);
    } else {
      setIsMuted(false);
    }
  };

  const handleMuteToggle = () => {
    if (audioElement) {
      if (isMuted) {
        audioElement.volume = volume;
        setIsMuted(false);
      } else {
        audioElement.volume = 0;
        setIsMuted(true);
      }
    }
  };

  const handleProgressChange = (event, newValue) => {
    if (!audioElement) return;
    
    const newTime = (newValue / 100) * duration;
    setProgress(newTime);
  };

  const handleProgressCommitted = (event, newValue) => {
    if (!audioElement) return;
    
    const newTime = (newValue / 100) * duration;
    audioElement.currentTime = newTime;
    setProgress(newTime);
    setIsDragging(false);
  };

  const handleProgressStart = () => {
    setIsDragging(true);
  };

  const formatTime = (timeInSeconds) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!currentSong) return null;

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        p: 2,
        backgroundColor: 'background.paper',
        zIndex: 1000,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Song Info */}
        <Box sx={{ minWidth: 180 }}>
          <Typography variant="subtitle1" noWrap>
            {currentSong.title}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {currentSong.artist || 'Unknown Artist'}
          </Typography>
        </Box>

        {/* Playback Controls */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <IconButton onClick={onPlayPause}>
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
          </Box>

          {/* Progress Bar */}
          <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption">{formatTime(progress)}</Typography>
            <Slider
              ref={progressRef}
              size="small"
              min={0}
              max={100}
              value={(progress / duration) * 100 || 0}
              onChange={handleProgressChange}
              onChangeCommitted={handleProgressCommitted}
              onMouseDown={handleProgressStart}
              onTouchStart={handleProgressStart}
              sx={{ mx: 2 }}
            />
            <Typography variant="caption">{formatTime(duration)}</Typography>
          </Box>
        </Box>

        {/* Volume Control */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 150 }}>
          <IconButton onClick={handleMuteToggle}>
            {isMuted || volume === 0 ? <VolumeOff /> : <VolumeUp />}
          </IconButton>
          <Slider
            size="small"
            min={0}
            max={100}
            value={isMuted ? 0 : volume * 100}
            onChange={handleVolumeChange}
            aria-label="Volume"
          />
        </Box>
      </Box>
    </Paper>
  );
};

export default MusicPlayer; 