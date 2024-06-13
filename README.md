<h1 align="center">
MusicBud </h1>

<h5 align="center">
 REST API matches users with similar taste in music based on Spotify API.
 </h5>

<h5 align="center">The project is in progress</h5>

### Demo link

http://152.70.49.208/musicbud/docs/


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

### Installing

1. install neo4j
  - using apt-get (install-and-configure-neo4j)[https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-neo4j-on-ubuntu-20-04]
  - using kubernetes (neo4j5-on-kubernetes)[https://github.com/synyx/neo4j5-on-kubernetes/tree/main] 
2. ```pip3 install requirements.txt```
3. change .env accordindly 
Hit `localhost/musicbud/docs`
