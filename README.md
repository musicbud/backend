# MusicBud

<div align="center">
  <h1>MusicBud</h1>
  <p>A REST API that matches users with similar music tastes based on the Spotify API.</p>
  <p><em>🎵 Find your music buddies! 🎵</em></p>
  <p><strong>Status:</strong> In Progress</p>
</div>

## 📖 Overview

MusicBud is a platform that connects people based on their musical preferences. Using data from Spotify and other music services, our algorithm identifies potential "music buddies" by analyzing listening habits, favorite artists, genres, and tracks. The system uses a sophisticated matching algorithm implemented on a Neo4j graph database to find connections between users.

[Demo Link](https://musicbud-demo.example.com)

## ✨ Features

### Matching Algorithm
- **Artist Matching**: Find users who share your favorite artists
- **Track Matching**: Connect with people who listen to the same tracks as you
- **Genre Matching**: Discover users with similar genre preferences
- **Combined Analysis**: Comprehensive matching using weighted preference analysis

### User Profiles
- **Profile Retrieval**: Get detailed user profile information
- **Profile Creation**: Set up your music profile with preferences and bio
- **Profile Updates**: Update your preferences, bio, and favorite tracks
- **Social Links**: Connect your profile with other music platforms

### Account Management
- **Authentication**: Secure login via Spotify OAuth
- **Token Management**: Automatic refresh token handling
- **Profile Synchronization**: Update your profile with latest Spotify data

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Neo4j Database (4.0+)
- Spotify Developer Account
- (Optional) Last.fm, YouTube Music, and MyAnimeList accounts for extended features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/musicbud.git
   cd musicbud
   ```

2. **Install Neo4j**
   - Using apt-get:
     ```bash
     sudo apt-get install neo4j
     ```
   - Or follow the [Neo4j installation guide](https://neo4j.com/docs/operations-manual/current/installation/)
   - For Kubernetes: [Neo4j Kubernetes guide](https://neo4j.com/docs/operations-manual/current/kubernetes/)

3. **Install Python requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file with your credentials (see Environment Configuration below)

5. **Run the application**
   ```bash
   python manage.py runserver
   ```
   The application will be available at http://127.0.0.1:8000/login

## 🔧 Environment Configuration

The application requires several API keys and configuration parameters. Copy the `.env.example` file to `.env` and configure the following:

### Required Credentials
- **Spotify API**: Register your app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
  - `SPOTIFY_CLIENT_ID`: Your Spotify client ID
  - `SPOTIFY_CLIENT_SECRET`: Your Spotify client secret
  - `SPOTIFY_REDIRECT_URI`: URL where Spotify will redirect after authentication

- **Neo4j Database**:
  - `NEO4J_URI`: Connection string (e.g., bolt://localhost:7687)
  - `NEO4J_USERNAME`: Database username (default: neo4j)
  - `NEO4J_PASSWORD`: Database password
  - `NEO4J_DATABASE`: Database name (for Neo4j 4.0+)

### Optional Credentials
- **Last.fm API**: Get API key at [Last.fm API](https://www.last.fm/api/account/create)
  - `LASTFM_API_KEY`: Your Last.fm API key
  - `LASTFM_API_SECRET`: Your Last.fm shared secret
  - `LASTFM_USERNAME`: Your Last.fm username (if required)

- **YouTube Music API**:
  - `YTMUSIC_HEADERS`: Headers for YouTube Music API
  - Or individual credentials: `YTMUSIC_COOKIE`, `YTMUSIC_AUTH`

- **MyAnimeList (MAL) API**: Register at [MyAnimeList API](https://myanimelist.net/apiconfig)
  - `MAL_CLIENT_ID`: Your MAL client ID
  - `MAL_CLIENT_SECRET`: Your MAL client secret
  - `MAL_REDIRECT_URI`: URL where MAL will redirect after authentication

### General Application Settings
- `SECRET_KEY`: Django secret key for cryptographic signing
- `DEBUG`: Set to True for development, False for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## 💻 Development

### Setting up Development Environment
1. Follow the installation steps above
2. Set `DEBUG=True` in your `.env` file
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Running the Development Server
```bash
python manage.py runserver
```

### Code Style
This project follows PEP 8 style guidelines. You can check your code with:
```bash
flake8 .
```

## 🧪 Testing

### Running Tests
```bash
python manage.py test
```

### Coverage Reports
```bash
coverage run --source='.' manage.py test
coverage report
```

## 📤 Deployment

### Production Setup
1. Set `DEBUG=False` in your `.env` file
2. Configure a proper production database
3. Set appropriate `ALLOWED_HOSTS`
4. Use a production-ready web server (Gunicorn, uWSGI, etc.)

### Example with Gunicorn and Nginx
1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Create a systemd service file
3. Configure Nginx as a reverse proxy
4. Set up SSL certificates

## 🔒 Security Practices

- **Never commit** your `.env` file to version control
- Keep API keys and secrets secure
- Rotate credentials regularly
- Use environment variables for all sensitive information
- Implement proper authentication and authorization
- Keep dependencies updated

### Recent Security Improvements
We've recently performed a comprehensive security audit and made the following improvements:

- Cleaned sensitive information from git history
- Implemented strict API key rotation policies
- Enhanced user authentication flow
- Added rate limiting to prevent abuse
- Updated all dependencies to address known vulnerabilities

## 👥 Contributing

We welcome contributions to MusicBud! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the coding standards.


### Demo link

http://84.235.170.234/


### Functions

<strong>Buds functions</strong>

Find buds profile with common:

- artists
- tracks
- artists,tracks and genres

<strong>User profile</strong>

- retrieve also set and update user and buds profiles including bio, tracks, and artists
  search
- searching for users and channels name

<strong>User account</strong>

- login
- refresh token
- update profile by replacing the old data from Spotify with the new one

<strong>using:</strong>
- python
- Django
- neo4j

### Environment Configuration

The application requires various API keys and credentials to function properly. Follow these steps to set up your environment:

1. **Copy the example environment file**:
   ```
   cp .env.example .env
   ```

2. **Obtain necessary API keys and credentials**:

   - **Spotify API**:
     - Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
     - Create a new application
     - Note your Client ID and Client Secret
     - Set the redirect URI in your Spotify app settings

   - **Last.fm API**:
     - Create an account at [Last.fm API](https://www.last.fm/api)
     - Register a new application to obtain your API key and shared secret

   - **YouTube Music API**:
     - Follow instructions at [YouTube Data API](https://developers.google.com/youtube/v3/getting-started)
     - Create credentials in the Google Cloud Console

   - **MyAnimeList (MAL) API**:
     - Visit [MyAnimeList API](https://myanimelist.net/apiconfig)
     - Register an application to get your client ID

   - **Neo4j Database**:
     - Set up your Neo4j instance (see installation instructions below)
     - Configure the connection URL, username, and password

3. **Update your `.env` file** with the obtained credentials

4. **Security notes**:
   - **NEVER commit your `.env` file to version control**
   - Keep your API keys and secrets secure
   - Regularly rotate credentials according to service providers' recommendations
   - The repository includes `.env` in `.gitignore` to prevent accidental commits

5. **Required vs Optional Configuration**:
   - Spotify credentials are required for core functionality
   - Last.fm, YouTube Music, and MAL are optional integrations
   - Neo4j is required for the user matching functionality

### Installing

1. install neo4j
  - using apt-get [install-and-configure-neo4j](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-neo4j-on-ubuntu-20-04)
  - using kubernetes [neo4j5-on-kubernetes](https://github.com/synyx/neo4j5-on-kubernetes/tree/main) 
2. ```pip3 install -r requirements.txt```
3. Ensure your `.env` file is properly configured (see Environment Configuration section)
4. Run the application and navigate to `127.0.0.1/login`


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

