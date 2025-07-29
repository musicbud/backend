# MusicBud

<div align="center">
  <h1>MusicBud</h1>
  <p>A REST API that matches users with similar music tastes based on the Spotify API.</p>
  <p><em>🎵 Find your music buddies! 🎵</em></p>
  <p><strong>Status:</strong> In Progress</p>
</div>

## 📖 Overview

MusicBud is a platform that connects people based on their musical preferences. Using data from Spotify and other music services, our algorithm identifies potential "music buddies" by analyzing listening habits, favorite artists, genres, and tracks. The system uses a sophisticated matching algorithm implemented on a Neo4j graph database to find connections between users.

## 🗄️ Databases

MusicBud uses two databases for optimal performance and scalability:

- **Neo4j (Graph Database):**
  Used for storing all music-related data, user preferences, and relationships. Powers the AI recommendation and matching engine.
  Configured via the `NEOMODEL_NEO4J_BOLT_URL` setting in your environment or `musicbud/settings.py`.

- **Relational Database (Default: SQLite):**
  Used for user authentication, login info, and Django admin data.
  By default, this is SQLite, but you can use PostgreSQL, MySQL, etc. by updating the `DATABASES` setting in `musicbud/settings.py`.

**How they work together:**
- User login and authentication are handled by Django’s relational database.
- All music and social graph data are managed in Neo4j.
- The app links users across both databases using unique identifiers (UIDs).

---

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

## 📚 API Documentation

A full Postman collection is available for exploring and testing all endpoints:
- [Download/Postman Collection (JSON)](./postman_collection/collection.json)

### API Categories

| Category                | Example Endpoints (see below for full list)                |
|-------------------------|-----------------------------------------------------------|
| **Buds**                | `/bud/profile`, `/bud/top/artists`, `/bud/liked/artists`  |
| **User Profile & Likes**| `/me/profile`, `/me/likes/update`, `/me/liked/artists`    |
| **Commonality**         | `/bud/common/liked/artists`, `/bud/common/top/tracks`     |
| **Service Connections** | `/spotify/connect`, `/ytmusic/connect`, `/mal/connect`    |
| **Authentication**      | `/login`, `/register`, `/logout`, `/token/refresh`        |
| **Search & Misc**       | `/bud/search`, `/merge-similars`                          |
| **Chat & Messaging**    | `/chat/`, `/chat/send_message/`, `/chat/create_channel/`  |

#### Example Endpoints by Category

**Buds**
- `/bud/profile` — Get bud profile
- `/bud/top/artists` — Get buds by top artists
- `/bud/top/tracks` — Get buds by top tracks
- `/bud/top/genres` — Get buds by top genres
- `/bud/top/anime` — Get buds by top anime
- `/bud/top/manga` — Get buds by top manga
- `/bud/liked/artists` — Get buds by liked artists
- ...

**User Profile & Likes**
- `/me/profile` — Get your profile
- `/me/profile/set` — Set your profile
- `/me/likes/update` — Update your likes
- `/me/liked/artists`, `/me/liked/tracks`, `/me/liked/genres`, `/me/liked/albums` — Get your liked items
- `/me/top/artists`, `/me/top/tracks`, `/me/top/genres`, `/me/top/anime`, `/me/top/manga` — Get your top items

**Commonality**
- `/bud/common/liked/artists`, `/bud/common/liked/tracks`, `/bud/common/liked/genres`, `/bud/common/liked/albums` — Get common liked items with buds
- `/bud/common/played/tracks` — Get common played tracks
- `/bud/common/top/artists`, `/bud/common/top/tracks`, `/bud/common/top/genres`, `/bud/common/top/anime`, `/bud/common/top/manga` — Get common top items

**Service Connections (OAuth)**
- `/service/login` — Start service login
- `/spotify/callback`, `/ytmusic/callback`, `/lastfm/callback`, `/mal/callback` — OAuth callbacks
- `/spotify/connect`, `/ytmusic/connect`, `/lastfm/connect`, `/mal/connect` — Connect to services
- `/ytmusic/token/refresh`, `/spotify/token/refresh` — Refresh tokens for services

**Authentication**
- `/register` — Register a new user
- `/logout` — Logout
- `/login` — Login
- `/token/refresh` — Refresh JWT token

**Search & Misc**
- `/bud/search` — Search users
- `/merge-similars` — Merge similar items
- `/spotify/seed/user/create` — Create user seed (for seeding/testing)

**Chat & Messaging**
- `/chat/` — Chat home
- `/chat/channel/<str:channel_name>/` — Channel chat
- `/chat/users/` — List users
- `/chat/user_chat/<int:user_id>/` — User-to-user chat
- `/chat/send_message/` — Send a message
- `/chat/create_channel/` — Create a new channel
- ...

For the full list and details, import the [Postman collection](./postman_collection/collection.json) into Postman or your preferred API client.

### 🤖 AI-Powered 'Get Common' Endpoints

These endpoints use AI and graph analysis to find items (artists, tracks, genres, etc.) that you and another user (bud) have in common. They require authentication and a `bud_id` in the request body.

**Base URL:** `/bud/common/`

| Endpoint                  | Description                                 |
|--------------------------|---------------------------------------------|
| liked/artists            | Common liked artists                        |
| liked/tracks             | Common liked tracks                         |
| liked/genres             | Common liked genres                         |
| liked/albums             | Common liked albums                         |
| played/tracks            | Common played tracks                        |
| top/artists              | Common top artists                          |
| top/tracks               | Common top tracks                           |
| top/genres               | Common top genres                           |
| top/anime                | Common top anime                            |
| top/manga                | Common top manga                            |

#### **Usage Example**

**Request:**
```http
POST /bud/common/liked/artists
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "bud_id": "<bud_user_uid>"
}
```

**Response:**
```json
{
  "results": [
    {
      "name": "Artist Name",
      "image": "https://...",
      // ...other artist fields
    },
    // ...more items
  ],
  "count": 10,
  "next": null,
  "previous": null
}
```

- Replace `liked/artists` with any of the endpoints above to get common tracks, genres, albums, etc.
- The `bud_id` is the unique identifier of the other user (bud) you want to compare with.
- The response is paginated and contains the common items and their details.

For more details and to test these endpoints, use the [Postman collection](./postman_collection/collection.json).

---

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

