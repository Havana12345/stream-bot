from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

# ====== ДАННЫЕ (через Railway Variables) ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
STREAMER_LOGIN = os.getenv("STREAMER_LOGIN")

# ====== СОСТОЯНИЕ ======
is_live = False
stream_start_time = None
max_viewers = 0
access_token = None


# ====== TELEGRAM ======
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, json=data)


# ====== TWITCH TOKEN ======
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


# ====== ПРОВЕРКА СТРИМА ======
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

            live_data = r.get("data", [])

            # ====== СТРИМ ОНЛАЙН ======
            if live_data:
                viewers = live_data[0]["viewer_count"]

                if viewers > max_viewers:
                    max_viewers = viewers

                if not is_live:
                    is_live = True
                    stream_start_time = datetime.utcnow()

                    send_message("🔴 Стрим начался! Залетай 💜")

            # ====== СТРИМ ОФФЛАЙН ======
            else:
                if is_live:
                    is_live = False

                    if stream_start_time:
                        duration = datetime.utcnow() - stream_start_time
                        minutes = duration.seconds // 60

                        send_message(
                            f"⚫ Стрим закончился!\n"
                            f"⏱ Длительность: {minutes} минут\n"
                            f"👀 Пик зрителей: {max_viewers}"
                        )

                    max_viewers = 0

        except Exception as e:
            print("error:", e)

        time.sleep(60)  # проверка раз в 60 секунд


# ====== FLASK ======
@app.route("/")
def home():
    return "Bot is running"


# ====== ЗАПУСК ФОНОВОГО ЧЕКА ======
threading.Thread(target=check_stream, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
