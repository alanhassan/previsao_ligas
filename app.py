import base64
from pickle import TRUE
import joblib
from io import BytesIO, StringIO
import requests
import pandas as pd
from PIL import Image
import streamlit as st
from github import Github
import requests
from bs4 import BeautifulSoup
import os

#token

key = os.environ.get('API_Key')
g = Github(key)

#repositório
repo = g.get_repo("alanhassan/previsao_ligas")

#get ml model from github
url_ml = 'https://github.com/alanhassan/previsao_ligas/blob/main/best_lr_pipeline.pkl?raw=true'

file = BytesIO(requests.get(url_ml).content)
ml = joblib.load(file)

# updated database with recent matches from github

url_df = 'https://github.com/alanhassan/previsao_ligas/blob/main/df_rolling.xlsx?raw=true'
data = requests.get(url_df).content
df = pd.read_excel(data)

# Function to add background photo
def add_bg_from_local(image_file, type = 'jpg'):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{type};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

# centralize image
def centralize_image(image, caption):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
                
    with col2:
        st.image(image, caption=caption)
                
    with col3:
        st.write(' ')

# func home
def home(df, team):
    df = df.sort_values(by=['date'])
    df = df[df['home'] == f'{team}'][-1:].drop(columns = ['date', 'comp', 'home', 'away',
                                                            'gf_rolling_away', 'ga_rolling_away',
                                                            'pont_rolling_away', 'Points last season_away',
                                                            'FIFA_23_Overall_away'], inplace=False)
    df.rename(columns={"gf_rolling_home": "gf_rolling",
                            "ga_rolling_home": "ga_rolling",
                            "pont_rolling_home": "pont_rolling",
                            "Points last season_home": "Points last season",
                        "FIFA_23_Overall_home": "FIFA_23_Overall"}, inplace=True)
    df = df[['Points last season', 'FIFA_23_Overall', 'pont_rolling', 'gf_rolling', 'ga_rolling']].reset_index(drop=True)
    return df

# func away
def away(df, team):
    df = df.sort_values(by=['date'])
    df = df[df['away'] == f'{team}'][-1:].drop(columns = ['date', 'comp', 'home', 'away',
                                                            'gf_rolling_home', 'ga_rolling_home',
                                                            'pont_rolling_home', 'Points last season_home',
                                                            'FIFA_23_Overall_home'], inplace=False)
    df.rename(columns={"gf_rolling_away": "gf_rolling",
                            "ga_rolling_away": "ga_rolling",
                            "pont_rolling_away": "pont_rolling",
                            "Points last season_away": "Points last season",
                        "FIFA_23_Overall_away": "FIFA_23_Overall"}, inplace=True)
    df = df[['Points last season', 'FIFA_23_Overall', 'pont_rolling', 'gf_rolling', 'ga_rolling']].reset_index(drop=True)
    df['pont_rolling'].replace(0, 1, inplace=True)
    df['gf_rolling'].replace(0, 1, inplace=True)
    df['ga_rolling'].replace(0, 1, inplace=True)
    return df

# func ratio
def ratio(df, team1, team2):
    df = home(df, f'{team1}')/away(df, f'{team2}')
    df.rename(columns={"Points last season": "points_last_season_ratio",
                        "FIFA_23_Overall": "FIFA_23_Overall_ratio",
                        "pont_rolling": "pont_rolling_ratio",
                        "gf_rolling": "gf_rolling_ratio",
                        "ga_rolling": "ga_rolling_ratio"}, inplace=True)
    return df

def add_logo(logo_url: str):
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"] {{
                background-image: url({logo_url});
                background-repeat: no-repeat;
                padding-top: 80px;
                background-position: 80px 80px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

########################################################################################

st.set_page_config(layout="centered", page_icon=":soccer:", page_title="Predictions")

blank, title_col, blank = st.columns([1,9,1])

#title_col.title("Quem será o vencedor?")
st.markdown(f'<h1 style="color:#000000;font-size:50px;">{"Who will be the winner?"}</h1>', unsafe_allow_html=True)
#background: rgba(240, 240, 240, 0.4)
#background-color:#0066cc
add_bg_from_local('background.jpg') 
add_logo("https://raw.githubusercontent.com/alanhassan/previsao_ligas/main/seriea.png")


with st.sidebar:
    
    # texto
    st.header('Select the options below:')

    # Competition
    league = df.comp.drop_duplicates().sort_values(ascending=True)
    league_choice = st.selectbox(
        "LEAGUE",
        league
    )

    # Time Casa
    teams_home = df.home.loc[df.comp == league_choice].drop_duplicates().sort_values(ascending=True)
    teams_home_choice = st.selectbox("HOME team", teams_home)

    # Time Fora
    teams_away = df.away.loc[df.comp == league_choice].drop_duplicates().sort_values(ascending=True)
    teams_away_choice = st.selectbox("AWAY team", teams_away)

    col1, col2 = st.columns(2)

    with col1:
        submit_button = st.button("Submit")    
    with col2:
        st.write(' ')


    last_date = str(df.date.max())[0:10]

    css_updt = """
    <style>
    [class="font2"]{
        font-family: 'Black';
        color: #000000;
        font-size: 14px;
    }
    </style>
    """
    st.markdown(css_updt, unsafe_allow_html=True)
    st.markdown(f'<p class="font2">Last game date: {last_date}</p>', unsafe_allow_html=True)



# If button is pressed
if submit_button:

    prediction = ml.predict_proba(ratio(df, teams_home_choice, teams_away_choice))[0][1]
    image_home = Image.open(f'{teams_home_choice.lower().replace(" ", "_")}.png')
    image_away = Image.open(f'{teams_away_choice.lower().replace(" ", "_")}.png')

    col1, col2, col3, col4 = st.columns(4)
    col1.image(image_home)
    col2.metric(teams_home_choice, f'{(prediction*100).round(2)}%')
    col3.image(image_away)
    col4.metric(teams_away_choice, f'{((1 - prediction)*100).round(2)}%')


home_FIFA_23_Overall = home(df, teams_home_choice)['FIFA_23_Overall'][0]
home_points_last_season = home(df, teams_home_choice)['Points last season'][0]
home_pont_rolling = home(df, teams_home_choice)['pont_rolling'][0]
home_gf_rolling = home(df, teams_home_choice)['gf_rolling'][0]
home_ga_rolling = home(df, teams_home_choice)['ga_rolling'][0]

away_FIFA_23_Overall = away(df, teams_away_choice)['FIFA_23_Overall'][0]
away_points_last_season = away(df, teams_away_choice)['Points last season'][0]
away_pont_rolling = away(df, teams_away_choice)['pont_rolling'][0]
away_gf_rolling = away(df, teams_away_choice)['gf_rolling'][0]
away_ga_rolling = away(df, teams_away_choice)['ga_rolling'][0]


if submit_button:
    with st.expander("Click for more information"):
        col1, col2 = st.columns(2)

        col1.caption(f'{teams_home_choice} (last 3 home games)')
        col2.caption(f'{teams_away_choice} (last 3 away games)')
        col1.text(f'FIFA 23 rating: {home_FIFA_23_Overall}')
        col1.text(f'Points last season: {home_points_last_season}')
        col1.text(f'Points: {home_pont_rolling}')
        col1.text(f'Goals scored: {home_gf_rolling}')
        col1.text(f'Goals conceded: {home_ga_rolling}')

        col2.text(f'FIFA 23 rating: {away_FIFA_23_Overall}')
        col2.text(f'Points last season: {away_points_last_season}')
        col2.text(f'Points: {away_pont_rolling}')
        col2.text(f'Goals scored: {away_gf_rolling}')
        col2.text(f'Goals conceded: {away_ga_rolling}')
