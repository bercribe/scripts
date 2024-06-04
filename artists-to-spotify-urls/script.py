import requests
import time

def get_spotify_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=payload, auth=(client_id, client_secret))
    return response.json().get('access_token')

def get_artist_spotify_url(artist_name, token):
    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    retries = 3
    backoff_factor = 2

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            artists = data['artists']['items']
            if artists:
                return artists[0]['external_urls']['spotify']
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Spotify URL for {artist_name} on attempt {attempt+1}: {e}")
            time.sleep(backoff_factor ** attempt)  # Exponential backoff
    return None

def read_artists_from_file(file_path):
    with open(file_path, 'r') as file:
        artists = [line.strip() for line in file if line.strip()]
    return artists

client_id = '70c949069b6a451eaa9064c2b42ec0f5'  # Replace with your Client ID
client_secret = '2477486dd99c4813926663b3bb3cf7af'  # Replace with your Client Secret
file_path = 'artists.txt'  # Path to the file containing artist names
output_file_path = 'spotify_urls.md'  # Path to the file where results will be saved

artists = read_artists_from_file(file_path)
token = get_spotify_token(client_id, client_secret)
if not token:
    print("Failed to retrieve access token")
else:
    with open(output_file_path, 'w') as file:
        for artist in artists:
            url = get_artist_spotify_url(artist, token)
            if url:
                file.write(f"[{artist}]({url})\n")
            else:
                file.write(f"{artist} not found!\n")
            file.flush()
