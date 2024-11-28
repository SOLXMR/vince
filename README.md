# Music Platform

A web application for downloading and managing music from Spotify. Built with Flask and React.

## Features

- User authentication
- Download songs from Spotify
- Convert songs to different formats (MP3/WAV)
- Personal music library management
- Modern, responsive UI

## Tech Stack

- **Backend**: Flask, MongoDB, yt-dlp, ffmpeg
- **Frontend**: React, Material-UI
- **Database**: MongoDB Atlas
- **Authentication**: JWT

## Setup

### Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB Atlas account
- Spotify Developer account
- ffmpeg

### Backend Setup

1. Clone the repository
```bash
git clone <your-repo-url>
cd music_platform/backend
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create .env file
```bash
cp .env.example .env
# Edit .env with your MongoDB URI, Spotify credentials, and JWT secret
```

5. Run the server
```bash
python app.py
```

### Frontend Setup

1. Navigate to frontend directory
```bash
cd music_platform/frontend
```

2. Install dependencies
```bash
npm install
```

3. Start development server
```bash
npm start
```

## Environment Variables

Create a `.env` file in the backend directory with the following:

```
MONGODB_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

## Deployment

### Backend (Vercel)

1. Install Vercel CLI
```bash
npm i -g vercel
```

2. Deploy
```bash
cd backend
vercel
```

### Frontend (Vercel)

1. Deploy
```bash
cd frontend
vercel
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 