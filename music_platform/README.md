# Music Platform - MP3 to WAV Converter

A web application that allows users to upload MP3 files and download them in WAV format. Built with Flask and React.

## Features

- User authentication and authorization
- MP3 to WAV conversion
- Song metadata extraction
- Search and filter songs
- Responsive UI
- Secure file handling

## Prerequisites

- Python 3.8+
- Node.js 14+
- FFmpeg (for audio conversion)

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
- On Ubuntu/Debian: `sudo apt-get install ffmpeg`
- On macOS: `brew install ffmpeg`
- On Windows: Download from https://ffmpeg.org/download.html

5. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the values in `.env` with your configuration

6. Initialize the database:
```bash
flask db upgrade
```

7. Run the development server:
```bash
flask run
```

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register a new user
- POST `/api/auth/login` - Login user
- GET `/api/auth/profile` - Get user profile

### Songs
- POST `/api/songs/upload` - Upload a new song
- GET `/api/songs/download/<id>` - Download a song
- GET `/api/songs/list` - List all songs
- DELETE `/api/songs/<id>` - Delete a song

## Security Considerations

1. Change the secret keys in production
2. Enable HTTPS in production
3. Implement rate limiting
4. Validate file types and sizes
5. Sanitize user inputs

## License

MIT License 