

# %%
import streamlit as st

import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials
import time

# -------------------------------
# CONFIG

ROOT_DIR = "data"
DATA_FILE = f"{ROOT_DIR}/sentences.csv"  # CSV with one column of sentences, no header
ANNOT_FILE = f"{ROOT_DIR}/annotations.csv"
SERVICE_ACCOUNT_FILE = "service_account.json"  # Google service account JSON
SHEET_NAME = "feuilleton_annotations"


# Create local annotations CSV if not exists
if not os.path.exists(ANNOT_FILE):
    pd.DataFrame(columns=["annotator", "text_id", "text", "sentiment_score"]).to_csv(ANNOT_FILE, index=False)

# -------------------------------
# LOAD SENTENCES
# -------------------------------
# If CSV, read directly
df = pd.read_csv(DATA_FILE, header=None, names=["text", "feuilleton_id"])
df['text'] = df['text'].astype(str)

# -------------------------------
# GOOGLE SHEETS AUTH
# -------------------------------

# Load service account from Streamlit secrets
creds_dict = dict(st.secrets["google_service_account"])
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

gc = gspread.authorize(creds)
sheet_url = "https://docs.google.com/spreadsheets/d/1kcPj-cGEBaCp1dDZDEt0pNlqkhZFYN5EaWWY1r2-LLY/edit?usp=sharing"
sheet = gc.open_by_url(sheet_url).sheet1

tmp = pd.DataFrame()

# -------------------------------
# STREAMLIT SESSION STATE
# -------------------------------
if "username" not in st.session_state:
    st.session_state.username = ""

if "idx" not in st.session_state:
    st.session_state.idx = 0

# -------------------------------
# SIDEBAR: USER INFO
# -------------------------------
st.sidebar.title("Deltager Info")
st.session_state.username = st.sidebar.text_input(
    "Navn eller initialer:", st.session_state.username
)


# -------------------------------
# START PAGE
# -------------------------------
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.title("Velkommen til annotering!")
    st.markdown("""
    **Instruktioner:**  
    Først: Indtast dit navn/initialer i sidebaren til venstre og tryk "enter". \n
    Derefter vil du se sætninger.  
    Læs hver sætning og vurder følelsen fra 0 (meget negativ) til 10 (meget positiv).  \n
    Prøv at lade være med at tænke for meget på konteksten - fokuser på den følelsesladning, der "ligger i" sætningen selv. \n
    Klik 'Start' når du er klar til at begynde.
    """)
    if st.button("Start"):
        st.session_state.started = True
        st.rerun()
else:
    # -------------------------------
# MAIN ANNOTATION AREA
# -------------------------------
    if st.session_state.idx >= len(df):
        st.success("🎉 Alle sætninger er annoterede. Tak for hjælpen!")

        # save leftover annotations if any
        if not st.session_state.tmp.empty:
            for r in st.session_state.tmp.values.tolist():
                sheet.append_row(r)
            st.session_state.tmp = pd.DataFrame()  # reset
            st.info("Alle dine annoteringer er nu gemt i Google Sheets ✅")
            
    else:
        # init timer and tmp in session_state
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()
        if "tmp" not in st.session_state:
            st.session_state.tmp = pd.DataFrame()

        row = df.iloc[st.session_state.idx]
        text_id, text = f"{row['feuilleton_id']}_{row.name}", row["text"]

        st.markdown(f"**Sætning {st.session_state.idx + 1} af {len(df)}**")
        st.markdown(f"<p style='font-size:24px'>{text}</p>", unsafe_allow_html=True)
        st.write("Scor sætningen efter følelse: 0 = meget negativ // 5 = neutral // 10 = meget positiv")
        score = st.slider("Score:", 0.0, 10.0, 5.0, step=0.5, key=f"slider_{st.session_state.idx}")

        if st.button("Gem"):
            if st.session_state.username.strip() == "":
                st.error("⚠️ Indtast venligst dit navn eller initialer i sidebar før du gemmer.")
            else:
                new_row = pd.DataFrame([{
                    "annotator": st.session_state.username,
                    "text_id": text_id,
                    "text": text,
                    "sentiment_score": score
                }])
                st.session_state.tmp = pd.concat([st.session_state.tmp, new_row], ignore_index=True)

                # check elapsed time
                elapsed_time = time.time() - st.session_state.start_time
                if elapsed_time > 120:  # flush to Google Sheets every 2 min
                    for r in st.session_state.tmp.values.tolist():
                        sheet.append_row(r)
                    st.session_state.tmp = pd.DataFrame()  # reset buffer
                    st.session_state.start_time = time.time()  # reset timer

                st.success("Gemt!")
                st.session_state.idx += 1
                st.rerun()

