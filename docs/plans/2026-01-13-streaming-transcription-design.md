# Streaming Transcription Design

**Date:** 2026-01-13
**Goal:** Reduce transcription delay from 5+ seconds to near real-time

## Problem

Current flow: record → stop → transcribe → type. This creates a 5+ second delay after speaking, making the app unusable for real work. Need to support all recording lengths from short phrases to long-form dictation.

## Solution

Replace batch transcription with streaming using RealtimeSTT library. Words appear as you speak.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DictationApp                          │
├─────────────────────────────────────────────────────────┤
│  Hotkey Listener (pynput)                               │
│      │                                                   │
│      ▼ Ctrl+Shift+D                                     │
│  ┌─────────────────────────────────────────────────────┐│
│  │  RealtimeSTT Recorder                               ││
│  │  - Manages audio stream internally                  ││
│  │  - Runs faster-whisper under the hood               ││
│  │  - Fires callbacks on partial/final text            ││
│  └─────────────────────────────────────────────────────┘│
│      │                                                   │
│      ▼ on_realtime_transcription_update                 │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Text Differ                                        ││
│  │  - Tracks what's been typed                         ││
│  │  - Calculates diff (new chars to type)              ││
│  │  - Handles backspaces for corrections               ││
│  └─────────────────────────────────────────────────────┘│
│      │                                                   │
│      ▼                                                   │
│  ydotool type / backspace                               │
└─────────────────────────────────────────────────────────┘
```

**Key changes:**
- Remove manual audio capture (sounddevice, queue, threading)
- Add text diffing logic for real-time corrections
- Keep same hotkey mechanism (Ctrl+Shift+D)

## Real-Time Typing Behavior

Whisper refines understanding as you speak. Example:

```
Time 0.5s: "I want to"        → types "I want to"
Time 1.0s: "I want to go"     → types " go"
Time 1.5s: "I wanted to go"   → backspaces "want to go", types "wanted to go"
```

**Text Differ logic:**

1. Track `last_typed` - what we've already typed
2. Compare new transcription to `last_typed`
3. Find common prefix (unchanged text)
4. Backspace changed portion, type new text

```python
last_typed = "I want to go"
new_text   = "I wanted to go"

common_prefix = "I want"
chars_to_delete = len(last_typed) - len(common_prefix)  # 6
chars_to_type = new_text[len(common_prefix):]  # "ed to go"

# Result: 6 backspaces, then type "ed to go"
```

**Safeguard:** Skip corrections requiring >20 backspaces to avoid chaotic UI.

## Control Flow

**Starting dictation:**
```
Ctrl+Shift+D → RealtimeSTT.start() → "[DICTATING] Speak now..."
Words appear in focused app as you speak
```

**Stopping dictation:**
```
Ctrl+Shift+D → RealtimeSTT.stop() → Wait for final callback
→ Type remaining text → "[DONE] Typed X words" → Reset differ
```

## Error Handling

| Scenario | Response |
|----------|----------|
| No microphone | Error at startup, exit |
| Mic disconnects | Stop gracefully, show error |
| ydotool fails | Pause transcription, show error |
| >20 backspaces needed | Skip correction, log warning |
| Long silence | VAD finalizes segment (built-in) |
| Ctrl+C | Stop recorder, finalize text, exit |

## Testing

**Manual scenarios:**
1. Short phrase - "Hello world"
2. Full sentence - natural speech
3. Pause mid-speech - 3s silence then continue
4. Rapid toggle - start/stop quickly
5. Long dictation - 60+ seconds

**Validation targets:**
- Latency: words appear within 0.5-1s
- Corrections: <5 backspaces per sentence typical
- CPU: under 50% sustained

## Dependencies

- RealtimeSTT (pip install RealtimeSTT)
- Keeps: pynput, ydotool
- Removes: sounddevice, manual audio queue management
