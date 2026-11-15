import os
import telebot
from flask import Flask, request

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"  # Твой токен
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# Универсальный роутик, который принимает любые запросы на корень или по пути вебхука
@app.route("/", methods=["GET", "POST"])
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get.data.decode("utf-8") if hasattr(request, 'data') else request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "", 200
    return "Bot is running!", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Бот успешно запущен и работает!")

if __name__ == "__main__":
    HOST_URL = "https://tg-bot-bekv.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
