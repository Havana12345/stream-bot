from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

# ===== VARIABLES (Railway) =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
STREAMER_LOGIN = os.getenv("STREAMER_LOGIN")

# ===== КАРТИНКА ДЛЯ СТАРТА =====
STREAM_IMAGE = "https://i.pinimg.com/736x/71/8f/71/718f71618efd1218d2c8b1d1f8ac174a.jpg"

# ===== STATE =====
is_live = False
stream_start_time = None
max_viewers = 0
access_token = None


# ===== TELEGRAM MESSAGE =====
def send_message(text, image=None, button=False):

    # ===== С КАРТИНКОЙ =====
    if image:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        data = {
            "chat_id": CHAT_ID,
            "photo": image,
            "caption": text,
            "parse_mode": "HTML"
        }

    # ===== ОБЫЧНОЕ СООБЩЕНИЕ =====
    else:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }

    # ===== КНОПКА =====
# ===== КНОПКА =====
if button:

    data["reply_markup"] = {
        "inline_keyboard": [
            [
                {
                    "text": "💜 Twitch",
                    "url": f"https://twitch.tv/{STREAMER_LOGIN}"
                },
                {
                    "text": "💙 VK Live",
                    "url": "https://live.vkvideo.ru/m1ss_sunshine"
                }
            ]
        ]
    }
# ===== TWITCH TOKEN =====
def get_token():

    global access_token

    url = "https://id.twitch.tv/oauth2/token"

    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    r = requests.post(url, params=params)

    access_token = r.json().get("access_token")


# ===== ПРОВЕРКА СТРИМА =====
def check_stream():

    global is_live, stream_start_time, max_viewers, access_token

    while True:

        try:

            if not access_token:
                get_token()

            url = f"https://api.twitch.tv/helix/streams?user_login={STREAMER_LOGIN}"

            headers = {
                "Client-ID": CLIENT_ID,
                "Authorization": f"Bearer {access_token}"
            }

            r = requests.get(url, headers=headers).json()

            data = r.get("data", [])

            # ===== СТРИМ НАЧАЛСЯ =====
            if data:

                viewers = data[0]["viewer_count"]

                if viewers > max_viewers:
                    max_viewers = viewers

                if not is_live:

                    is_live = True
                    stream_start_time = datetime.utcnow()

                    send_message(
                        '<tg-emoji emoji-id="5348299705992374531">⚡️</tg-emoji> '
                        '<b>M1ss_Sunshine мурчит в эфире</b> '
                        '<tg-emoji emoji-id="5348299705992374531">⚡️</tg-emoji>\n\n'
                        'Залетай на стрим и приятного просмотра '
                        '<tg-emoji emoji-id="5348110581402461749">💜</tg-emoji>',
                        image=STREAM_IMAGE,
                        button=True
                    )

            # ===== СТРИМ ЗАКОНЧИЛСЯ =====
            else:

                if is_live:

                    is_live = False

                    if stream_start_time:

                        duration = datetime.utcnow() - stream_start_time

                        total_minutes = duration.seconds // 60
                        hours = total_minutes // 60
                        minutes = total_minutes % 60

                        duration_text = f"{hours}:{minutes:02}"

                        send_message(
                            '<tg-emoji emoji-id="5348587443031403178">⭐️</tg-emoji> '
                            '<b>M1ss_Sunshine закончила стрим</b> '
                            '<tg-emoji emoji-id="5348587443031403178">⭐️</tg-emoji>\n\n'
                            '<tg-emoji emoji-id="5345840253099864159">⌛️</tg-emoji> '
                            f'Длительность стрима: <b>{duration_text}</b>\n'
                            '<tg-emoji emoji-id="5345913576781539831">🐱</tg-emoji> '
                            f'Зрители: <b>{max_viewers}</b>\n\n'
                            '<tg-emoji emoji-id="5348118424012745224">💜</tg-emoji> '
                            'Спасибо всем, кто был на стриме '
                            '<tg-emoji emoji-id="5348118424012745224">💜</tg-emoji>'
                        )

                    max_viewers = 0

        except Exception as e:

            print("error:", e)

        # ===== ПРОВЕРКА КАЖДУЮ МИНУТУ =====
        time.sleep(15)


# ===== ROUTE =====
@app.route("/")
def home():
    return "Bot is running"


# ===== ФОНОВЫЙ ПОТОК =====
threading.Thread(target=check_stream, daemon=True).start()



# ===== ЗАПУСК =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
