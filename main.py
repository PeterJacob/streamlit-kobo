import re
import sqlite3
from datetime import datetime
from pathlib import Path

import deepl
import streamlit as st
from elevenlabs.client import ElevenLabs

from anki_export import AnkiConnectError, export_to_anki


def get_default_start_datetime() -> str:
    """Return the default start datetime string from kobo_date.txt."""
    with open("kobo_date.txt", "r") as text_file:
        return text_file.read().strip()


def is_valid_datetime(s: str) -> bool:
    """Check if a string is a valid ISO datetime."""
    try:
        datetime.fromisoformat(s)
        return True
    except ValueError:
        return False


def clean_text(text: str) -> str:
    cleaned = "".join(c for c in text if c.isprintable() or c == " ")
    cleaned = re.sub(r" +", " ", cleaned).strip()
    if cleaned and cleaned[0].isalpha() and not cleaned[0].isupper():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned and cleaned[-1] not in ".!?;:…":
        cleaned += "."
    return cleaned


def get_kobo_highlights(start_datetime: str) -> tuple[list[str], str]:
    """Retrieve highlighted sentences from Kobo since start_datetime.

    Returns a tuple of (highlights, max_date).
    """
    con = sqlite3.connect(st.secrets["kobo_db_path"])
    cur = con.cursor()

    # https://www.reddit.com/r/kobo/comments/sy9xe4/export_kobo_highlights_and_notes_automatically/
    s = f"""
    select Text, DateCreated
    from Bookmark
    where Type IN ("highlight", "note") and DateCreated > "{start_datetime}"
    order by DateCreated desc
    """

    res = cur.execute(s)
    lines = res.fetchall()
    con.close()

    max_date = str(lines[0][1])
    return [clean_text(text) for text, _ in lines], max_date


def translate_sentences(sentences: list[str], target_lang: str) -> list[str]:
    translator = deepl.Translator(st.secrets["deepl_api_key"])
    results = translator.translate_text(sentences, target_lang=target_lang)
    return [r.text for r in results]


def get_elevenlabs_client() -> ElevenLabs:
    return ElevenLabs(api_key=st.secrets["elevenlabs_api_key"])


@st.cache_data
def get_voices() -> dict[str, str]:
    """Return a dict mapping voice name to voice_id."""
    client = get_elevenlabs_client()
    response = client.voices.get_all()
    return {v.name: v.voice_id for v in response.voices}


def generate_tts(sentences: list[str], voice_id: str, output_dir: Path) -> list[str]:
    """Generate TTS audio files for each sentence. Returns list of file paths."""
    client = get_elevenlabs_client()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    progress = st.progress(0, text="Generating TTS audio...")
    for i, sentence in enumerate(sentences):
        progress.progress(
            i / len(sentences),
            text=f"Generating TTS audio ({i + 1}/{len(sentences)})...",
        )
        audio = client.text_to_speech.convert(
            text=sentence,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"tts_{timestamp}_{i}.mp3"
        with open(path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        paths.append(str(path))
    progress.empty()
    return paths


st.title("Kobo → Anki Flashcards")

if st.session_state.get("export_success"):
    st.success(st.session_state.export_success)
    st.session_state.export_success = None

if "sentences" not in st.session_state:
    st.session_state.sentences = None

if "_pending_start_datetime" in st.session_state:
    st.session_state.start_datetime_input = st.session_state._pending_start_datetime
    del st.session_state._pending_start_datetime

if "start_datetime_input" not in st.session_state:
    st.session_state.start_datetime_input = get_default_start_datetime()

start_datetime = st.text_input("Highlights since", key="start_datetime_input")

if not is_valid_datetime(start_datetime):
    st.error("Invalid datetime format. Use ISO format, e.g. 2026-02-09T21:03:31.000")

if st.button("Load Kobo Highlights", disabled=not is_valid_datetime(start_datetime)):
    highlights, st.session_state.max_date = get_kobo_highlights(start_datetime)
    translations = translate_sentences(highlights, "NL")
    st.session_state.sentences = [
        {"sentence": h, "translation": t, "selected": True}
        for h, t in zip(highlights, translations)
    ]
    for i, t in enumerate(translations):
        st.session_state[f"trans_{i}"] = t

if st.session_state.sentences is not None:
    for i, item in enumerate(st.session_state.sentences):
        selected = st.checkbox(
            "Select",
            value=item["selected"],
            key=f"sel_{i}",
            label_visibility="collapsed",
        )
        st.session_state.sentences[i]["selected"] = selected
        sentence = st.text_area(
            "Sentence",
            value=item["sentence"],
            key=f"sent_{i}",
            label_visibility="collapsed",
        )
        st.session_state.sentences[i]["sentence"] = sentence
        if st.button("Translate", key=f"translate_{i}"):
            new_translation = translate_sentences(
                [st.session_state[f"sent_{i}"]], "NL"
            )[0]
            st.session_state.sentences[i]["translation"] = new_translation
            st.session_state[f"trans_{i}"] = new_translation
        translation = st.text_area(
            "Translation", key=f"trans_{i}", label_visibility="collapsed"
        )
        st.session_state.sentences[i]["translation"] = translation
        st.divider()

    if st.button("Add sentence"):
        st.session_state.sentences.append(
            {"sentence": "", "translation": "", "selected": True}
        )
        st.rerun()

    voices = get_voices()
    preferred = [v for v in st.secrets["preferred_voices"] if v in voices]
    other = sorted(v for v in voices if v not in preferred)
    voice_options = [f"★ {v}" for v in preferred] + other
    selected_label = st.selectbox("TTS Voice", options=voice_options)
    selected_voice = selected_label.removeprefix("★ ")

    if st.button("TTS and export to Anki"):
        selected_items = [s for s in st.session_state.sentences if s["selected"]]
        sentences_to_speak = [s["sentence"] for s in selected_items]
        voice_id = voices[selected_voice]
        output_dir = Path("tts_output")
        audio_paths = generate_tts(sentences_to_speak, voice_id, output_dir)
        flashcards = [
            {
                "sentence": item["sentence"],
                "translation": item["translation"],
                "audio_path": audio_path,
            }
            for item, audio_path in zip(selected_items, audio_paths)
        ]
        try:
            export_to_anki(flashcards)
            with open("kobo_date.txt", "w") as text_file:
                text_file.write(st.session_state.max_date)
            st.session_state.export_success = (
                f"Generated {len(audio_paths)} audio files and exported to Anki."
            )
            for key in list(st.session_state.keys()):
                if key.startswith(("sel_", "sent_", "trans_", "translate_")):
                    del st.session_state[key]
            st.session_state.sentences = None
            st.session_state._pending_start_datetime = st.session_state.max_date
            st.session_state.max_date = None
            st.rerun()
        except AnkiConnectError as e:
            st.error(f"Anki export failed: {e}")
