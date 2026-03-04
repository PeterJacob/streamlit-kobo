# Kobo → Anki Flashcards

A Streamlit app to aid language learning by bridging your Kobo e-reader, DeepL, ElevenLabs, and Anki.

**Workflow:** highlight a sentence on your Kobo → open the app → get a Dutch translation via DeepL → generate spoken audio via ElevenLabs TTS → export as an Anki flashcard with audio.

## Project structure

```
app.py                         # Native desktop launcher (PyWebView)
main.py                        # Streamlit app (UI and orchestration)
anki_export.py                 # AnkiConnect integration
setup_py2app.py                # py2app bundling config
kobo_date.txt                  # Timestamp of last successful export
.streamlit/secrets.toml        # API keys and config (not in repo)
.streamlit/secrets.toml.example  # Template for secrets.toml
pyproject.toml                 # Dependencies (managed with uv)
tts_output/                    # Generated MP3 files (not in repo)
```

## Requirements

- [Kobo Desktop Edition](https://www.kobo.com/desktop) installed and synced (provides the local SQLite database)
- [Anki](https://apps.ankiweb.net/) running with the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on
- A [DeepL API](https://www.deepl.com/pro-api) key
- An [ElevenLabs](https://elevenlabs.io/) API key
- [uv](https://github.com/astral-sh/uv) for dependency management

## Installation

1. Clone the repo:
   ```
   git clone https://github.com/PeterJacob/streamlit-kobo.git
   cd streamlit-kobo
   ```

2. Install dependencies:
   ```
   uv sync
   ```

3. Copy the secrets template and fill in your values:
   ```
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   Edit `.streamlit/secrets.toml`:
   ```toml
   kobo_db_path = "/path/to/Kobo Desktop Edition/Kobo.sqlite"
   deepl_api_key = "your-deepl-api-key"
   elevenlabs_api_key = "your-elevenlabs-api-key"
   preferred_voices = [
       "Voice Name 1",
       "Voice Name 2",
   ]
   ```

   The Kobo SQLite database is typically found at:
   - **macOS:** `~/Library/Application Support/Kobo/Kobo Desktop Edition/Kobo.sqlite`
   - **Windows:** `%APPDATA%\Kobo\Kobo Desktop Edition\Kobo.sqlite`

4. Run the app as a native desktop window:
   ```
   uv run python app.py
   ```

   Or run as a regular Streamlit app in the browser:
   ```
   uv run streamlit run main.py
   ```

## Building a .app bundle (macOS)

To create a standalone `.app` you can put in your Applications folder or Dock:

```
uv pip install py2app
python setup_py2app.py py2app
```

The `.app` bundle will be created in the `dist/` directory.

To add a custom icon, place an `icon.icns` file in the project root and uncomment the `iconfile` line in `setup_py2app.py`.

## Usage

1. Make sure Anki is open with AnkiConnect running.
2. Launch the app (double-click the `.app` bundle, or run `uv run python app.py`).
3. The "Highlights since" field is pre-filled with the timestamp of your last export. Adjust if needed.
4. Click **Load Kobo Highlights** to fetch and translate your recent highlights.
5. Review, edit, or remove sentences as needed.
6. Select a TTS voice and click **TTS and export to Anki** to generate audio and create flashcards in your `ZZZ_inbox` deck.
