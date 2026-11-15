import telebot

TOKEN = "9213726416:AAHSKz3sdyxo05XS-yX0dH_1h6FGg7PKA_k"  # Вставь свой токен
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Бот успешно запущен и работает в локальном режиме!")

if __name__ == "__main__":
    print("Запуск бота в режиме Long Polling...")
    bot.remove_webhook()
    bot.infinity_polling()