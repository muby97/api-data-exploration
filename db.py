import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

def fetch_artist_tags(artist, api_key):
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={artist}&api_key={api_key}&format=json"
    response = requests.get(url)
    return response.json()

def safe_get_artist_name(artist_dict):
    """Safely extract the artist name from the given dictionary."""
    return artist_dict.get('#text', 'Unknown Artist') if isinstance(artist_dict, dict) else 'Unknown Artist'

def display_recent_tracks_artworks(recent_tracks_data):
    """Display artwork of the last 6 tracks with rounded edges and spacing, along with song titles and artist names."""
    if 'recenttracks' in recent_tracks_data and 'track' in recent_tracks_data['recenttracks']:
        tracks = recent_tracks_data['recenttracks']['track']
        # Ensure there are at least 6 tracks
        tracks = tracks[:6]
        
        # Extract image URLs, titles, and artist names
        images = [track.get('image', [{}])[-1].get('#text') for track in tracks]
        titles = [track.get('name') for track in tracks]
        artists = [safe_get_artist_name(track.get('artist', {})) for track in tracks]
        
        # Display artworks with titles and artist names
        st.markdown("<h3 style='text-align: center;'>Recently Listened Songs</h3>", unsafe_allow_html=True)
        cols = st.columns(len(images))
        for col, image, title, artist in zip(cols, images, titles, artists):
            if image:  # Ensure there's an image URL
                col.markdown(f"""
                    <div style='text-align: center;'>
                        <img src="{image}" style='border-radius: 15px; width: 100px; height: 100px; margin: 5px;'>
                        <p style='margin: 0; font-weight: bold;'>{title}</p>
                        <p style='margin: 0;'>{artist}</p>
                    </div>
                """, unsafe_allow_html=True)

        # Apply custom styling for spacing and rounded edges
        st.markdown(
            """
            <style>
            .stImage {
                border-radius: 15px;
                margin: 5px;
            }
            </style>
            """, unsafe_allow_html=True
        )

def main():
    st.title("Last.fm Data Visualization Dashboard")
    
    user = st.text_input("Enter Last.fm Username:")
    if not user:
        st.warning("Please enter a Last.fm username.")
        return

    limit = st.slider("Number of Top Artists to Display:", 1, 50, 10)
    
    # Fetch data
    top_artists_data = fetch_top_artists(user, API_KEY, limit)
    recent_tracks_data = fetch_user_tracks(user, API_KEY, limit)

    # Extract artist names for the dropdown
    if top_artists_data and 'topartists' in top_artists_data:
        artist_names = [artist['name'] for artist in top_artists_data['topartists']['artist']]
    else:
        artist_names = []

    # Display statistics in gradient color cards side by side
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if top_artists_data and 'topartists' in top_artists_data:
                artist_count = len(top_artists_data['topartists']['artist'])
                st.markdown(f"<div style='padding: 10px; background: linear-gradient(to right, #FFAFBD, #ffc3a0); color: white; border-radius: 8px;'>Artists: {artist_count}</div>", unsafe_allow_html=True)

        with col2:
            if recent_tracks_data and 'recenttracks' in recent_tracks_data:
                track_count = len(recent_tracks_data['recenttracks']['track'])
                st.markdown(f"<div style='padding: 10px; background: linear-gradient(to right, #2193b0, #6dd5ed); color: white; border-radius: 8px;'>Tracks: {track_count}</div>", unsafe_allow_html=True)

        with col3:
            if recent_tracks_data and 'recenttracks' in recent_tracks_data:
                album_count = len(set(track.get('album', {}).get('#text', '') for track in recent_tracks_data['recenttracks']['track']))
                st.markdown(f"<div style='padding: 10px; background: linear-gradient(to right, #FFA07A, #FF4500); color: white; border-radius: 8px;'>Albums: {album_count}</div>", unsafe_allow_html=True)

    # Display recent tracks' artwork
    display_recent_tracks_artworks(recent_tracks_data)

    # First Row: Listening Frequency by Hour (Spline Graph)
    if recent_tracks_data and 'recenttracks' in recent_tracks_data:
        tracks = recent_tracks_data['recenttracks']['track']
        df_tracks = pd.DataFrame(tracks)
        df_tracks['hour'] = pd.to_datetime(df_tracks['date'].apply(lambda x: x.get('#text') if isinstance(x, dict) else None), errors='coerce').dt.hour
        hour_counts = df_tracks['hour'].value_counts().sort_index()
        
        # Prepare data for spline plot
        hours = np.arange(0, 24)
        frequencies = [hour_counts.get(hour, 0) for hour in hours]
        
        # Create figure
        fig = go.Figure()

        # Add trace with gradient effect
        fig.add_trace(go.Scatter(
            x=hours,
            y=frequencies,
            mode='lines+markers',
            line=dict(color='rgba(255, 102, 102, 0.8)', width=4, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(255, 102, 102, 0.3)'  # Gradient effect
        ))

        # Update layout for background color and axis titles
        fig.update_layout(
            title="Listening Frequency by Hour (Spline Graph)",
            xaxis_title="Hour of the Day",
            yaxis_title="Frequency",
            # plot_bgcolor='rgba(240, 240, 240, 0.8)',  # Background color of the graph area
            # paper_bgcolor='white'  # Background color of the entire plotting area (optional)
        )
        
        # Display the figure
        st.plotly_chart(fig)
    
    if top_artists_data and 'topartists' in top_artists_data:
        artists_df = pd.DataFrame(top_artists_data['topartists']['artist'])
        artists_df['playcount'] = pd.to_numeric(artists_df['playcount'], errors='coerce')
        
        red_to_blue = [[0, 'red'], [1, 'blue']]
        
        fig = px.bar(
            artists_df,
            x='name',
            y='playcount',
            title="Top Artists Playcount",
            labels={'name': 'Artist', 'playcount': 'Playcount'},
            color='playcount',
            color_continuous_scale='tealrose'  # Gradient color from yellow to brown
        )
        st.plotly_chart(fig)

    # Second Row: 3D Stream Graph-like Visualization Comparing Streaming Habits Across Regions/Countries
    regions = ['North America', 'Europe', 'Asia', 'South America', 'Africa', 'Oceania']
    countries = ['USA', 'UK', 'Germany', 'Japan', 'Brazil', 'Nigeria', 'Australia']
    data = np.random.rand(len(countries), len(regions)) * 1000
    
    fig = go.Figure(data=[go.Surface(
        z=data,
        x=countries,
        y=regions,
        colorscale='Viridis',
        cmin=0,
        cmax=np.max(data)
    )])

    fig.update_layout(
        title="Streaming Habits Across Regions/Countries (3D Surface Plot)",
        scene=dict(
            xaxis_title='Country',
            yaxis_title='Region',
            zaxis_title='Streams'
        )
    )
    st.plotly_chart(fig)

    # Third Row: Artists Top tracks as 
    with st.container():
        artist = st.selectbox("Select Artist for Top Tracks:", artist_names)
        if artist:
            top_tracks_data = fetch_top_tracks(artist, API_KEY)
            top_tracks = top_tracks_data.get('toptracks', {}).get('track', [])
            
            if top_tracks:
                tracks_df = pd.DataFrame(top_tracks)
                tracks_df["playcount"] = pd.to_numeric(tracks_df["playcount"], errors='coerce')
                bins = 24  # Example bin number for a radial histogram
                counts, edges = np.histogram(tracks_df["playcount"], bins=bins)

                theta = np.linspace(0.0, 2 * np.pi, bins, endpoint=False)
                fig = go.Figure(
                    go.Barpolar(
                        r=counts,
                        theta=theta * 180/np.pi,
                        width=360/bins,
                        marker_color=np.linspace(0, 1, bins),
                        marker_line_color="black",
                        marker_line_width=2,
                        opacity=0.8,
                    )
                )
                fig.update_layout(
                    title=f"Radial Histogram of Top Tracks by {artist}",
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, max(counts)]),
                        angularaxis=dict(tickmode="array", tickvals=np.arange(0, 360, 360/bins))
                    ),
                    showlegend=False,
                )
                st.plotly_chart(fig)

                # Display top 8 tracks marquee
                top_8_tracks = tracks_df.head(8)
                marquee_content = " | ".join([f"{row['name']} ({row['playcount']} plays)" for index, row in top_8_tracks.iterrows()])
                
                # HTML for marquee
                marquee_html = f"""
                <style>
                    .marquee {{
                        width: 100%;
                        overflow: hidden;
                        white-space: nowrap;
                        box-sizing: border-box;
                        background-color: #f0f0f0;
                        padding: 10px 0;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    }}
                    .marquee span {{
                        display: inline-block;
                        padding-left: 100%;
                        animation: marquee 15s linear infinite;
                    }}
                    @keyframes marquee {{
                        0% {{ transform: translateX(100%); }}
                        100% {{ transform: translateX(-100%); }}
                    }}
                </style>
                <div class="marquee">
                    <span>{marquee_content}</span>
                </div>
                """
                st.markdown(marquee_html, unsafe_allow_html=True)

    # Fourth Row: Similar Artists as Bubble-Packed Circle
    with st.container():
        artist = st.selectbox("Select Artist for Similar Artists:", artist_names)
        if artist:
            similar_artists_data = fetch_similar_artists(artist, API_KEY)
            similar_artists = similar_artists_data.get('similarartists', {}).get('artist', [])
            
            if similar_artists:
                artists_df = pd.DataFrame(similar_artists)
                artists_df['match'] = pd.to_numeric(artists_df['match'], errors='coerce')

                fig = px.treemap(
                    artists_df,
                    path=['name'],
                    values='match',
                    color='match',
                    color_continuous_scale='RdBu',
                    title=f"Similar Artists to {artist} (Bubble-Packed Circle)",
                )
                fig.update_traces(marker=dict(showscale=False), textinfo="label+value")
                st.plotly_chart(fig)
    # Fifth Row: Genre Popularity Over Time
    with st.container():
        genre_tracks_data = fetch_genre_tracks(user, API_KEY)
        recent_tracks = genre_tracks_data['recenttracks']['track']
        df_genres = pd.DataFrame(recent_tracks)
        df_genres['artist_name'] = df_genres['artist'].apply(safe_get_artist_name)

        def get_top_genres(df):
            all_genres = []
            for artist in df['artist_name'].unique():
                tags_data = fetch_artist_tags(artist, API_KEY)
                tags = [tag['name'] for tag in tags_data.get('toptags', {}).get('tag', [])[:5]]
                all_genres.extend(tags)
            genre_series = pd.Series(all_genres)
            # Limit to top 8 genres
            return genre_series.value_counts().head(8).index.tolist()

        top_genres = get_top_genres(df_genres)
        df_genres['tags'] = df_genres['artist_name'].apply(lambda artist: ', '.join([tag['name'] for tag in fetch_artist_tags(artist, API_KEY).get('toptags', {}).get('tag', []) if tag['name'] in top_genres]))

        df_genres['date'] = pd.to_datetime(df_genres['date'].apply(lambda x: x.get('#text') if isinstance(x, dict) else None), errors='coerce')
        df_genres.dropna(subset=['date'], inplace=True)
        df_genres.set_index('date', inplace=True)

        # Filter to top 8 tags
        top_tags = df_genres['tags'].str.split(', ', expand=True).stack().value_counts().head(8).index
        df_genres = df_genres[df_genres['tags'].apply(lambda x: any(tag in x for tag in top_tags))]

        # Streamgraph-like plot
        df_tags_grouped = df_genres.groupby([df_genres.index, 'tags']).size().unstack().fillna(0)

        # Resample data weekly to smooth out the trends
        df_tags_grouped = df_tags_grouped.resample('W').mean()

        # Dropdown menu for genre selection
        all_tags = df_tags_grouped.columns.tolist()
        selected_tags = st.multiselect(
            "Select genres to display:",
            options=all_tags,
            default=all_tags[:5]  # Default to the first 5 genres
        )

        fig = go.Figure()

        for tag in selected_tags:
            if tag in df_tags_grouped.columns:
                fig.add_trace(go.Scatter(
                    x=df_tags_grouped.index,
                    y=df_tags_grouped[tag],
                    mode='lines',
                    stackgroup='one',
                    name=tag
                ))

        fig.update_layout(
            title="Genre Popularity Over Time (Top 8 Tags)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
    