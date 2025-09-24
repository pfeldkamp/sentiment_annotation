

# %%
import streamlit as st

import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials


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
    Først: Indtast dit navn/initialer i sidebar og tryk "enter".
    Derefter vil du se sætninger.  
    Læs sætningen og vurder følelsen fra 0 (meget negativ) til 10 (meget positiv).  \n
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
    else:
        row = df.iloc[st.session_state.idx]
        text_id, text = f"{row['feuilleton_id']}_{row.name}", row["text"]

        st.markdown(f"**Sætning {st.session_state.idx + 1} af {len(df)}**")
        st.markdown(f"<p style='font-size:24px'>{text}</p>", unsafe_allow_html=True)
        st.write("Scor sætningen efter følelse, hvor: 0 = meget negativ // 5 = neutral // 10 = meget positiv")
        score = st.slider("Score:", 0.0, 10.0, 5.0, step=0.5)

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
                new_row.to_csv(ANNOT_FILE, mode="a", header=False, index=False)
                sheet.append_row([st.session_state.username, text_id, text, score])
                st.success("Gemt!")
                st.session_state.idx += 1
                st.rerun()

# # -------------------------------
# # MAIN ANNOTATION AREA
# # -------------------------------
# if st.session_state.idx >= len(df):
#     st.success("🎉 Alle sætninger er annoterede. Tak for hjælpen!")
# else:
#     # Current sentence
#     row = df.iloc[st.session_state.idx]
#     text_id, text = f"{row['feuilleton_id']}_{row.name}", row["text"]

#     # Progress
#     st.markdown(f"**Sætning {st.session_state.idx + 1} af {len(df)}**")

#     # Big text display
#     st.markdown(f"<p style='font-size:24px'>{text}</p>", unsafe_allow_html=True)

#     # Instructions
#     st.write("Scor sætningen efter følelse, hvor: 0 = meget negativ // 5 = neutral // 10 = meget positiv")

#     # Decimal slider
#     score = st.slider("Score:", 0.0, 10.0, 5.0, step=0.5)

#     # Submit button
#     if st.button("Gem"):
#         if st.session_state.username.strip() == "":
#             st.error("⚠️ Indtast venligst dit navn eller initialer i sidebar før du gemmer.")
#         else:
#             # Save locally
#             new_row = pd.DataFrame([{
#                 "annotator": st.session_state.username,
#                 "text_id": text_id,
#                 "text": text,
#                 "sentiment_score": score
#             }])
#             new_row.to_csv(ANNOT_FILE, mode="a", header=False, index=False)

#             # Save to Google Sheets
#             sheet.append_row([
#                 st.session_state.username,
#                 text_id,
#                 text,
#                 score
#             ])

#             st.success("Gemt!")

#             # Move to next sentence
#             st.session_state.idx += 1
#             st.rerun()
