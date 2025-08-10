import telebot
import sqlite3
import threading
import time
import os
from flask import Flask

TOKEN = "8210719359:AAHQ6wOHWdOzHTuiRoD1GXxwT0SqlED6ihk"
ADMIN_ID = 7717315369

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======== БАЗА ДАННЫХ ========
def init_db():
    conn = sqlite3.connect("services.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price INTEGER
                )''')
    conn.commit()
    conn.close()

def add_service(name, price):
    conn = sqlite3.connect("services.db")
    c = conn.cursor()
    c.execute("INSERT INTO services (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()

def get_services():
    conn = sqlite3.connect("services.db")
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM services")
    data = c.fetchall()
    conn.close()
    return data

def update_price(service_id, new_price):
    conn = sqlite3.connect("services.db")
    c = conn.cursor()
    c.execute("UPDATE services SET price=? WHERE id=?", (new_price, service_id))
    conn.commit()
    conn.close()

# ======== БОТ ========
@bot.message_handler(commands=["start"])
def start(message):
    services = get_services()
    if not services:
        bot.send_message(message.chat.id, "Пока нет доступных услуг.")
    else:
        text = "📚 Доступные услуги:\n"
        for s in services:
            text += f"{s[0]}. {s[1]} — {s[2]}₽\n"
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["add"])
def admin_add(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введи название услуги:")
        bot.register_next_step_handler(msg, get_service_name)
    else:
        bot.send_message(message.chat.id, "⛔ У тебя нет доступа!")

def get_service_name(message):
    service_name = message.text
    msg = bot.send_message(message.chat.id, "Введи цену:")
    bot.register_next_step_handler(msg, lambda m: save_service(m, service_name))

def save_service(message, service_name):
    try:
        price = int(message.text)
        add_service(service_name, price)
        bot.send_message(message.chat.id, f"✅ Услуга '{service_name}' добавлена за {price}₽")
    except:
        bot.send_message(message.chat.id, "❌ Цена должна быть числом.")

@bot.message_handler(commands=["price"])
def change_price(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введи ID услуги и новую цену через пробел:")
        bot.register_next_step_handler(msg, update_service_price)
    else:
        bot.send_message(message.chat.id, "⛔ У тебя нет доступа!")

def update_service_price(message):
    try:
        service_id, new_price = map(int, message.text.split())
        update_price(service_id, new_price)
        bot.send_message(message.chat.id, "✅ Цена изменена!")
    except:
        bot.send_message(message.chat.id, "❌ Неверный формат. Пример: `1 500`")

# ======== КОСТЫЛЬ ДЛЯ RENDER ========
@app.route('/')
def keep_alive():
    return "Bot is running!"

def ping_self():
    while True:
        try:
            os.system("curl https://YOUR-RENDER-URL.onrender.com")
        except:
            pass
        time.sleep(600)  # пингуем каждые 10 мин

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot).start()
    threading.Thread(target=ping_self).start()
    app.run(host="0.0.0.0", port=10000)
