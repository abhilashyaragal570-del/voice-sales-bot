# Riya: AI Voice Sales Bot

Built for the **Sankar Group Intern Assignment: Build an AI Voice Sales Bot**.

Riya is an AI sales agent that holds a real voice conversation with a customer in the browser. She speaks, listens, answers questions, explains the SaaS product, and tries to convert the customer. After the call she saves the recording, writes an AI summary and assigns a sales status.

**Live demo:** https://voice-sales-bot.onrender.com
**Repository:** https://github.com/abhilashyaragal570-del/voice-sales-bot

> The free Render tier sleeps when idle. The first load can take up to a minute, so please wait for the page to appear.

---

## Table of Contents

1. [Assignment Requirements Covered](#assignment-requirements-covered)
2. [Features](#features)
3. [How It Works](#how-it-works)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Run Locally](#run-locally)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [How to Test the Demo](#how-to-test-the-demo)
10. [Sales Statuses](#sales-statuses)
11. [Limitations and Notes](#limitations-and-notes)
12. [Future Improvements](#future-improvements)
13. [Author](#author)

---

## Assignment Requirements Covered

| # | Requirement | How it is met |
| --- | --- | --- |
| 1 | Voice conversation | Browser speech recognition listens to the customer and speech synthesis speaks Riya's replies. The AI model answers questions, explains the product and drives toward a sale. |
| 2 | Language | English, Hindi and Telugu, chosen from a language selector. |
| 3 | Live chat screen | Riya's messages and the customer's replies appear as text in real time. |
| 4 | Call controls | Start Call and End Call buttons, with call duration and call status. |
| 5 | Call recording | The call is recorded after the customer gives consent, saved when the call ends, and can be played back. |
| 6 | AI summary | A short summary with customer requirements, objections and next steps is generated automatically. |
| 7 | Sales status | One of six statuses is assigned automatically. |
| 8 | Call history | Previous calls are listed with recording, summary, transcript and final status. |

## Features

- Real two-way voice conversation, not a prerecorded script
- Live transcript of both sides during the call
- Start Call and End Call buttons, live timer and status indicator
- Recording consent shown before the call begins
- Recording saved after the call with a playback option
- Automatic AI summary: customer requirements, objections, next steps
- Automatic sales status classification
- Call history page with recording, summary, transcript and status for each call
- Female voice preference with an automatic fallback depending on the device's voices
- Retry handling when an AI tool call fails, so the call does not break

## How It Works

```
Customer clicks Start Call and accepts recording consent
        |
Customer speaks
        |
Browser speech recognition converts speech to text
        |
Text is sent to the FastAPI backend (app.py)
        |
AI model generates Riya's sales reply
        |
Reply is shown in the live chat and spoken by the browser
        |
Customer clicks End Call
        |
Recording is saved, transcript is stored
        |
AI generates the summary and assigns the sales status
        |
Call appears in Call History
```

Speech recognition and Riya's voice run in the customer's browser. The server handles the conversation logic, summary, status and storage.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| AI model | Any OpenAI-compatible chat completions API, set through environment variables |
| Frontend | HTML, CSS, JavaScript (single page) |
| Speech | Browser Web Speech API for recognition and synthesis |
| Recording | Browser MediaRecorder API |
| Hosting | Render |
| Version control | Git and GitHub |

## Project Structure

```
voice-sales-bot/
|-- app.py              # FastAPI app: routes, AI conversation, summary, status
|-- requirements.txt    # Python dependencies
|-- static/
|   |-- index.html      # Frontend: call UI, live chat, recording, history
|-- .gitignore          # Excludes .env, .venv and cache files
|-- README.md
```

## Run Locally

### Prerequisites

- Python 3.10 or newer
- An API key for the AI provider
- Chrome or Edge on desktop with a working microphone

### Steps

```powershell
git clone https://github.com/abhilashyaragal570-del/voice-sales-bot.git
cd voice-sales-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:LLM_BASE_URL = "https://your-provider-url/v1"
$env:LLM_API_KEY = "your_key_here"
$env:LLM_MODEL = "your_model_name"
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 and allow microphone access when asked.

## Configuration

| Variable | Purpose |
| --- | --- |
| `LLM_BASE_URL` | Base URL of an OpenAI-compatible chat completions API |
| `LLM_API_KEY` | API key for the provider |
| `LLM_MODEL` | Model name to use |
| `LLM_REASONING` | Optional reasoning effort setting |

Never commit keys to the repository. Set them as environment variables locally and in the Render dashboard.

## Deployment

The app runs on Render as a web service.

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** add the API key under the Environment tab
- **Updating:** push to `main`, then choose Manual Deploy and Deploy latest commit

## How to Test the Demo

1. Open the live link in Chrome or Edge on a desktop.
2. Choose a language: English, Hindi or Telugu.
3. Read and accept the recording consent.
4. Click **Start Call** and allow the microphone.
5. Talk to Riya. Ask about pricing, features, or raise an objection such as "it is too expensive".
6. Watch the live chat, timer and status update.
7. Click **End Call**.
8. Review the summary, sales status and recording playback.
9. Open **Call History** to see the saved call.

## Sales Statuses

Each call is assigned exactly one status:

- **Converted**: the customer agreed to buy
- **Interested**: positive interest, no commitment yet
- **Follow-up Required**: customer needs more time or information
- **Not Interested**: customer declined
- **Demo Requested**: customer asked for a demo
- **No Response**: the customer did not respond during the call

## Limitations and Notes

- **Voices depend on the device.** Edge usually has the most natural female voices (such as Neerja and Aria). If no female voice exists for the language, the app raises the pitch as a fallback.
- **Telugu voice** needs a Telugu voice installed in Windows (Settings > Time & language > Speech). Otherwise a default voice is used.
- **The recording captures only the customer's microphone**, not Riya's voice.
- **Browser support:** speech recognition works best in Chrome and Edge. Firefox and Safari have limited support.
- **Storage:** on the free Render tier, files on disk can be lost when the service restarts, so older calls may not persist.
- **Cold start:** the first request after idle time is slow on the free tier.

## Future Improvements

- Server-side text-to-speech for the same voice on every device
- Recording of both sides of the call
- Persistent database and cloud storage for recordings
- Analytics dashboard for calls and conversion rate
- More languages and product knowledge bases

## Author

**Abhilash Yaragal**
GitHub: [@abhilashyaragal570-del](https://github.com/abhilashyaragal570-del)
