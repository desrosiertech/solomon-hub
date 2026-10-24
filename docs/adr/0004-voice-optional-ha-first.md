# Voice is optional; Home Assistant owns the pipeline

Solomon works with the microphone off. When voice is enabled, Home Assistant Assist is the speech pipeline (wake word, STT, local intents, TTS). Hermes answers only the leftover household questions, through the same Tools the web chat uses. There is no ambient recording in Solomon, and no public voice endpoint.

**Status:** accepted (planning). Hardware for satellites is open.

## How it works with voice disabled

Chat is a page in Solomon. Food Corrections are taps. Device toggles are HA entities on the Devices view. The dashboard, meals, shopping list and calendars never call STT/TTS.

## Pipeline when enabled

```
button or on-device wake word
  → HA Assist satellite (LAN)
  → local STT (Speech-to-Phrase first, Whisper if the NLU needs it)
  → local intents for exposed entities  ("prefer handling commands locally")
  → else Solomon chat Tool  (Hermes or the app's own NLU)
  → Piper TTS
```

**[documented]** Assist is wake word + STT + conversation + TTS: https://www.home-assistant.io/voice_control/voice_remote_local_assistant/  
**[documented]** "Prefer handling commands locally" tries HA intents before an LLM: https://www.home-assistant.io/voice_control/assist_create_open_ai_personality/  
**[documented]** HA Ollama can control *exposed* entities only, and HA marks that **experimental**: https://www.home-assistant.io/integrations/ollama/

Device and safety-critical actions stay on the HA intent path (or a confirmed Solomon Tool), never on a free-form Hermes guess.

## Wake word disclosure

If a wake word is used, a powered microphone **must listen locally** for that phrase.

- **On-device (preferred):** microWakeWord on Voice PE / ESP32-S3. Audio leaves the device only after the wake word. Voice PE has a **physical mute switch that cuts power to the microphone**. **[documented]** https://www.home-assistant.io/voice-pe/ and https://www.home-assistant.io/voice_control/about_wake_word/#about-on-device-wake-word-processing-microwakeword
- **Server-side (avoid on shared rooms):** openWakeWord. Satellites stream audio to HA whenever they think they hear voice, so the mic is live on the LAN. **[documented]** https://www.home-assistant.io/voice_control/about_wake_word/
- **Push-to-talk (best for privacy):** ESPHome `voice_assistant.start` on a held button, or Voice PE center-click (tap-to-talk, not hold). **[documented]** https://esphome.io/components/voice_assistant/

Default recommendation: **push-to-talk, hardware mute, no wake word**. If a wake word is added, it is on-device only, English-only today, and Solomon still offers a software "voice off" that stops the satellite.

Audio retention: HA debug recordings are **opt-in** (`debug_recording_dir`). **[documented]** https://www.home-assistant.io/voice_control/troubleshooting/  
Default in-memory buffer length is **not documented**. Assume "held only for the utterance" and do not write audio unless a Member turns debug on.

## Rejected as the default

- Hermes gadget plugin on a public WebSocket (the friend's hub). No public ingress.
- Discord voice. Optional, with a warning that audio leaves the house.
- Cloud STT/TTS.
- Always-on openWakeWord in the kitchen.

The friend's ESP32 push-to-talk gadget is a fine *device*, used as an HA satellite rather than a Hermes gadget.
