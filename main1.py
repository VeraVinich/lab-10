import requests
import json
import random
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer

API_URL = "https://v2.jokeapi.dev/joke/Any?safe-mode"
MODEL_PATH = "model"

tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 0.9)

current_joke = None
current_joke_type = None
current_joke_category = None

def speak(text):
    print(f"[Ассистент]: {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()

def fetch_new_joke():
    global current_joke, current_joke_type, current_joke_category
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current_joke_category = data.get("category", "неизвестно")
        current_joke_type = data.get("type", "неизвестно")
        
        if current_joke_type == "single":
            current_joke = data.get("joke", "Шутка не найдена")
        elif current_joke_type == "twopart":
            setup = data.get("setup", "")
            delivery = data.get("delivery", "")
            current_joke = f"{setup} ... {delivery}"
        else:
            current_joke = "Не удалось получить шутку"
        
        return True
    except requests.exceptions.RequestException as e:
        speak("Ошибка при получении шутки.")
        print(f"Ошибка API: {e}")
        return False

def get_joke_type():
    if current_joke_type == "single":
        return "однострочная"
    elif current_joke_type == "twopart":
        return "диалог"
    else:
        return "неизвестно"

def get_joke_category():
    if current_joke_category:
        categories_ru = {
            "Programming": "программирование",
            "Misc": "разное",
            "Dark": "чёрный юмор",
            "Pun": "каламбур",
            "Spooky": "страшные",
            "Christmas": "рождественские"
        }
        return categories_ru.get(current_joke_category, current_joke_category.lower())
    return "неизвестно"

def read_joke():
    if current_joke:
        speak(current_joke)
    else:
        speak("Сначала создайте шутку командой 'создать'")

def save_joke_to_file():
    if not current_joke:
        speak("Нет шутки для сохранения. Сначала создайте шутку командой 'создать'")
        return False
    
    try:
        with open("jokes.txt", "a", encoding="utf-8") as f:
            f.write(f"Категория: {get_joke_category()}\n")
            f.write(f"Тип: {get_joke_type()}\n")
            f.write(f"Шутка: {current_joke}\n")
            f.write("-" * 50 + "\n")
        speak("Шутка записана в файл jokes.txt")
        return True
    except Exception as e:
        speak("Ошибка при записи в файл.")
        print(f"Ошибка записи: {e}")
        return False

def init_recognizer():
    try:
        model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(model, 16000)
        return recognizer
    except Exception as e:
        print(f"Ошибка загрузки модели Vosk: {e}")
        print("Убедитесь, что папка 'model' существует и содержит файлы модели")
        return None

def listen_command(recognizer):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=4000)
    
    print("Слушаю команду...")
    speak("Слушаю")
    
    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    return text.lower()
    except KeyboardInterrupt:
        print("\nПрерывание")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    return ""

def process_command(cmd):
    cmd = cmd.lower()
    
    if cmd == "создать":
        if fetch_new_joke():
            speak("Новая шутка создана")
        else:
            speak("Не удалось создать шутку")
    
    elif cmd == "тип":
        joke_type = get_joke_type()
        speak(f"Тип шутки: {joke_type}")
    
    elif cmd == "прочесть":
        read_joke()
    
    elif cmd == "категория":
        category = get_joke_category()
        speak(f"Категория шутки: {category}")
    
    elif cmd == "записать":
        save_joke_to_file()
    
    elif cmd in ["выход", "стоп", "завершить", "пока"]:
        speak("До свидания!")
        return False
    
    else:
        speak("Команда не распознана. Попробуйте: создать, тип, прочесть, категория, записать")
    
    return True

def main():
    print("Голосовой ассистент (шутки) запущен.")
    speak("Ассистент для генерации шуток запущен. Скажите команду.")
    
    recognizer = init_recognizer()
    if recognizer is None:
        print("Не удалось загрузить распознаватель речи. Завершение работы.")
        return
    
    while True:
        command = listen_command(recognizer)
        if command:
            print(f"[Распознано]: {command}")
            if not process_command(command):
                break

if __name__ == "__main__":
    main()