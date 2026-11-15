import os
import telebot
from flask import Flask, request

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# Роут для приема вебхуков от Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "", 200
    return "Forbidden", 403

# Проверочный роут, чтобы Render видел, что сервер живой
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Бот на Render успешно запущен и работает через вебхук!")

if __name__ == "__main__":
    HOST_URL = "https://tg-bot-bekv.onrender.com"
    
    # Автоматическая привязка вебхука при старте
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    
    # Запуск Flask на порту, который требует Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
