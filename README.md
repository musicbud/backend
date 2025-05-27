<h1 align="center">
MusicBud </h1>

<h5 align="center">
 REST API matches users with similar taste in music based on Spotify API.
 </h5>

<h5 align="center">The project is in progress</h5>

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
