import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import networkx as nx

# Set your Last.fm API key here
API_KEY = 'c706f5bd1cff553f928f8d08d988a6e4'

def fetch_top_artists(user, api_key, limit=10):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={user}&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    return response.json()

def fetch_user_tracks(user, api_key, limit=200):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    return response.json()

def fetch_similar_artists(artist, api_key, limit=10):
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={artist}&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    return response.json()

def fetch_top_tracks(artist, api_key, limit=10):
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    return response.json()

def fetch_genre_tracks(user, api_key, limit=200):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    return response.json()

def main():
    st.title("Last.fm Data Visualization Dashboard")
    
    user = st.text_input("Enter Last.fm Username:")
    if not user:
        st.warning("Please enter a Last.fm username.")
        return
    
    limit = st.slider("Number of Top Artists to Display:", 1, 50, 10)
    
    # Fetch data
    st.subheader("Fetching data from Last.fm...")
    top_artists_data = fetch_top_artists(user, API_KEY, limit)
    recent_tracks_data = fetch_user_tracks(user, API_KEY, limit)
    
    # Top Artists Analysis
    # st.subheader("Top Artists Data (Raw JSON)")
    # st.json(top_artists_data)
    
    if 'topartists' in top_artists_data and 'artist' in top_artists_data['topartists']:
        artists = top_artists_data['topartists']['artist']
        artists_df = pd.DataFrame(artists)
        
        # st.subheader("Top Artists Data (DataFrame)")
        # st.write(artists_df)
        
        if 'name' in artists_df.columns and 'playcount' in artists_df.columns:
            st.subheader(f"Top {limit} Artists for {user}")
            # st.write(artists_df[['name', 'playcount']])
            
            # Bar Chart for Top Artists
            fig = px.bar(artists_df, x='name', y='playcount', title='Top Artists Playcount')
            st.plotly_chart(fig)
        else:
            st.warning("Columns 'name' and 'playcount' not found in Top Artists data.")
    else:
        st.error("Top artists data not found.")
    
    # Recent Tracks Visualization
    # st.subheader("Recent Tracks Data (Raw JSON)")
    # st.json(recent_tracks_data)
    
    recent_tracks = recent_tracks_data.get('recenttracks', {}).get('track', [])
    
    # st.subheader("Recent Tracks Data (List)")
    # st.write(recent_tracks)
    
    if isinstance(recent_tracks, list) and len(recent_tracks) > 0:
        tracks_df = pd.json_normalize(recent_tracks)
        
        # st.subheader("Recent Tracks Data (DataFrame)")
        # st.write(tracks_df)
        
        if 'date' in tracks_df.columns:
            tracks_df['date'] = pd.to_datetime(tracks_df['date'].apply(lambda x: x['#text'] if isinstance(x, dict) and '#text' in x else None))
            tracks_df.set_index('date', inplace=True)
            track_counts = tracks_df['name'].resample('D').count()
            
            st.subheader("Listening Trend Over Time")
            fig, ax = plt.subplots()
            track_counts.plot(ax=ax, kind='line', title='Daily Listening Trends')
            st.pyplot(fig)
        else:
            st.warning("The 'date' column is not found in Recent Tracks data.")
    else:
        st.warning("Recent tracks data is empty or not in the expected format.")
    
    # Artist Similarity Analysis
    artist = st.text_input("Enter Artist Name for Similar Artists:")
    if artist:
        st.subheader(f"Similar Artists to {artist}")
        similar_artists_data = fetch_similar_artists(artist, API_KEY)
        similar_artists = similar_artists_data.get('similarartists', {}).get('artist', [])
        
        if similar_artists:
            artists_df = pd.DataFrame(similar_artists)
            st.write(artists_df)
            
            # Network Graph for Similar Artists
            G = nx.Graph()
            G.add_node(artist)
            for sim_artist in similar_artists:
                G.add_node(sim_artist['name'])
                G.add_edge(artist, sim_artist['name'])
            
            fig, ax = plt.subplots(figsize=(10, 7))
            pos = nx.spring_layout(G, seed=42)
            nx.draw(G, pos, with_labels=True, ax=ax, node_size=3000, node_color='skyblue', font_size=10, font_weight='bold', edge_color='gray')
            ax.set_title(f"Network of Similar Artists to {artist}")
            st.pyplot(fig)
        else:
            st.warning("No similar artists data available.")
    
    # Top Tracks by Artist
    artist = st.text_input("Enter Artist Name for Top Tracks:")
    if artist:
        st.subheader(f"Top Tracks by {artist}")
        top_tracks_data = fetch_top_tracks(artist, API_KEY)
        top_tracks = top_tracks_data.get('toptracks', {}).get('track', [])
        
        if top_tracks:
            tracks_df = pd.DataFrame(top_tracks)
            st.write(tracks_df[['name', 'playcount']])
            
            # Pie Chart for Top Tracks
            fig = px.pie(tracks_df, names='name', values='playcount', title=f'Top Tracks by {artist}')
            st.plotly_chart(fig)
        else:
            st.warning("No top tracks data available.")
    
    # Genre Popularity Over Time
    st.subheader("Genre Popularity Over Time")
    genre_tracks_data = fetch_genre_tracks(user, API_KEY)
    recent_tracks = genre_tracks_data.get('recenttracks', {}).get('track', [])
    
    if isinstance(recent_tracks, list) and len(recent_tracks) > 0:
        tracks_df = pd.json_normalize(recent_tracks)
        if 'date' in tracks_df.columns:
            tracks_df['date'] = pd.to_datetime(tracks_df['date'].apply(lambda x: x['#text'] if isinstance(x, dict) and '#text' in x else None))
            tracks_df.set_index('date', inplace=True)
            
            genres = [track.get('artist', {}).get('tags', {}).get('tag', []) for track in recent_tracks]
            genres_flat = [genre for sublist in genres for genre in sublist]
            genres_df = pd.DataFrame(genres_flat)
            
            genre_counts = genres_df['name'].value_counts()
            fig = px.pie(genre_counts, names=genre_counts.index, values=genre_counts.values, title="Genre Popularity")
            st.plotly_chart(fig)
        else:
            st.warning("Date column is not available in recent tracks data.")
    else:
        st.warning("Recent tracks data is empty or not in the expected format.")
    
    # User Listening Trends
    def display_user_listening_trends(user):
        recent_tracks_data = fetch_user_tracks(user, API_KEY, limit=200)
        recent_tracks = recent_tracks_data.get('recenttracks', {}).get('track', [])
        
        if isinstance(recent_tracks, list) and len(recent_tracks) > 0:
            tracks_df = pd.json_normalize(recent_tracks)
            if 'date' in tracks_df.columns:
                tracks_df['date'] = pd.to_datetime(tracks_df['date'].apply(lambda x: x['#text'] if isinstance(x, dict) and '#text' in x else None))
                tracks_df.set_index('date', inplace=True)
                track_counts = tracks_df['name'].resample('D').count()
                
                st.subheader("Listening Trend Over Time")
                fig, ax = plt.subplots()
                track_counts.plot(ax=ax, kind='line', title='Daily Listening Trends')
                st.pyplot(fig)
            else:
                st.warning("Date column is not available in recent tracks data.")
        else:
            st.warning("Recent tracks data is empty or not in the expected format.")
    
    # Artist Scrobble Trends
    def display_artist_scrobble_trends(user, artist_name):
        recent_tracks_data = fetch_user_tracks(user, API_KEY, limit=200)
        recent_tracks = recent_tracks_data.get('recenttracks', {}).get('track', [])
        
        if isinstance(recent_tracks, list) and len(recent_tracks) > 0:
            tracks_df = pd.json_normalize(recent_tracks)
            if 'date' in tracks_df.columns and 'artist' in tracks_df.columns:
                tracks_df['date'] = pd.to_datetime(tracks_df['date'].apply(lambda x: x['#text'] if isinstance(x, dict) and '#text' in x else None))
                tracks_df.set_index('date', inplace=True)
                
                artist_tracks_df = tracks_df[tracks_df['artist.name'] == artist_name]
                scrobble_counts = artist_tracks_df['name'].resample('D').count()
                
                st.subheader(f"Scrobble Trend for {artist_name}")
                fig, ax = plt.subplots()
                scrobble_counts.plot(ax=ax, kind='area', title=f'{artist_name} Scrobble Trend')
                st.pyplot(fig)
            else:
                st.warning("Date column is not available in recent tracks data.")
        else:
            st.warning("Recent tracks data is empty or not in the expected format.")

    # User Listening Trends
    st.subheader(f"Listening Trends for {user}")
    if user:
        display_user_listening_trends(user)
    
    # Artist Scrobble Trends
    artist_name = st.text_input("Enter Artist Name for Scrobble Trends:")
    if user and artist_name:
        display_artist_scrobble_trends(user, artist_name)

if __name__ == "__main__":
    main()
