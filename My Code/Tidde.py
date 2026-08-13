# ------------------- Imports -------------------
import speech_recognition as sr
from gtts import gTTS
import pywhatkit
import datetime
import wikipedia
import webbrowser
import random
import json
import time
import os
import tempfile
import threading
import pygame
from rapidfuzz import fuzz  # wake word fuzzy match

# ------------------- Setup -------------------
listener = sr.Recognizer()
active = True  # assistant active/pause control

# Load personality lines
with open("responses.json", "r", encoding="utf-8") as f:
    responses = json.load(f)

# Wake words (tidde variations)
WAKE_WORDS = ["tidde", "teddy", "tiddy", "td", "kitty", "did you", "tide", "3d", "siri", "teri", "ted", "didi"]

# ------------------- Speak Function -------------------
def talk(text):
    """Fast, safe, non-blocking TTS using pygame"""
    def _speak():
        try:
            temp_file = os.path.join(tempfile.gettempdir(), f"tidde_{time.time()}.mp3")
            tts = gTTS(text=text, lang='en')
            tts.save(temp_file)

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.unload()
            os.remove(temp_file)
        except Exception as e:
            print("TTS Error:", e)

    threading.Thread(target=_speak, daemon=True).start()

# ------------------- Wake Word Detector -------------------
def is_wake_word(text):
    text = text.lower()
    for word in WAKE_WORDS:
        if fuzz.partial_ratio(word, text) > 75:
            return True
    return False

# ------------------- Take Command -------------------
def take_command():
    try:
        with sr.Microphone() as source:
            print("🎤 Listening...")
            listener.adjust_for_ambient_noise(source, duration=0.5)
            audio = listener.listen(source)
            command = listener.recognize_google(audio).lower()
            print("🗣 You said:", command)
            return command
    except Exception:
        return ""

# ------------------- Main Run Function -------------------
def run_tidde():
    global active
    command = take_command()
    if not command:
        return

    # Only process if active
    if not active:
        print("(Assistant paused — waiting for wake word)")
        return

    # -------- Wake word detected --------
    if is_wake_word(command):
        # Do not auto-greet, just acknowledge
        talk("Yes? How can I help you?")

    # ------------------- Pause / Resume -------------------
    if "close" in command or "pause" in command:
        talk(random.choice(responses["farewells"]))
        active = False
        return

    if "start" in command or "resume" in command:
        talk(random.choice(responses["greetings"]))
        active = True
        return

    # ------------------- Play Song -------------------
    if "play" in command:
        song = command.replace("play", "").strip()
        talk(f"Playing {song}")
        try:
            threading.Thread(target=lambda: pywhatkit.playonyt(song), daemon=True).start()
        except:
            talk("Sorry, I couldn’t connect to YouTube right now.")

    # ------------------- Time -------------------
    elif "time" in command:
        time_now = datetime.datetime.now().strftime("%I:%M %p")
        print("Current time is", time_now)
        talk("Current time is " + time_now)

    # ------------------- Date -------------------
    elif "date" in command:
        today = datetime.datetime.now().strftime("%d %B %Y")
        print("Today is", today)
        talk("Today is " + today)

    # ------------------- Wikipedia Search -------------------
    elif "tell me about" in command or "details about" in command or "search" in command:
        topic = command.replace("tell me about", "").replace("details about", "").replace("search", "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2, auto_suggest=True, redirect=True)
            print(summary)
            talk(summary)
            threading.Thread(target=lambda: webbrowser.open(wikipedia.page(topic).url), daemon=True).start()
        except wikipedia.exceptions.PageError:
            talk("Sorry, I couldn't find results for " + topic)
        except Exception as e:
            print("Wiki Error:", e)
            talk("Something went wrong while searching Wikipedia.")

    # ------------------- Joke -------------------
    elif "joke" in command:
        joke = random.choice(responses["jokes"])
        print(joke)
        talk(joke)

    # ------------------- Fun -------------------
    elif "are you single" in command:
        response = "I am in a relationship with Wi-Fi"
        print(response)
        talk(response)

    # ------------------- Stop / Exit -------------------
    elif "stop" in command or "exit" in command:
        talk(random.choice(responses["farewells"]))
        time.sleep(2)
        exit()

    else:
        talk("Please say the command again.")

# ------------------- Main Loop -------------------
while True:
    run_tidde()
