# this file permalink: https://github.com/FuhrerStein/WhoIsWorking_bot/raw/master/Who_bot.py, https://bit.ly/2OHzezY


import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, User

print("Starting bot...")

with open("bot_key.key") as who_file:
    who_key = who_file.read()

with open("allow_chats.txt") as allow_file:
    allow_chats = allow_file.readlines()

allow_chats = [line.strip for line in allow_chats]

print(f"Active chat IDs: {allow_chats}")

bot = telebot.TeleBot(who_key)
messages_list = ['На лінії',
                 'Робоча пауза - наряд',
                 'Робоча пауза - дзвінок',
                 'Робоча пауза - пропущені',
                 'Робоча пауза - тікет',
                 'Робоча пауза - інше',
                 'Обід',
                 'Перерва',
                 'Кінець зміни',
]

status_groups = {0: 'На лінії',
                 1: 'Робоча перерва',
                 2: 'Перерва',
                 }

messages_db = {}

buttons_shown = False

for index, message_full in enumerate(messages_list):
    message_short = message_full.replace(' ', '_').casefold().replace("робоча_пауза_-", "рп")
    message_group = 3 if index == len(messages_list) - 1 else 0 if index == 0 else 2
    if message_short[:2] == "рп":
        message_group = 1
    messages_db[message_short] = (message_group, message_full)


people_list = {}


def online_buttons():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    button_counts = [0, 0, 0]
    for short_status in people_list.values():
        status_group = messages_db[short_status][0]
        button_counts[status_group] += 1

    inline_buttons = []
    for i in range(3):
        inline_buttons.append(InlineKeyboardButton(f"{status_groups[i]}: {button_counts[i]}", callback_data=f"cb_group{i}"))
    markup.add(*inline_buttons)
    return markup


def get_user_name(user: telebot.types.User):
    if user.first_name:
        if user.last_name:
            return user.first_name + " " + user.last_name
        else:
            return user.first_name
    elif user.last_name:
        return user.last_name
    elif user.username:
        return user.username
    else:
        return "Unnamed alien"


@bot.message_handler(commands=messages_db.keys())
def send_status(message):
    if not str(message.chat.id) in allow_chats:
        return

    user_name = get_user_name(message.from_user)
    command_clean = message.text[1:].split("@")[0]
    if command_clean in messages_db.keys():
        if messages_db[command_clean][0] == 3:
            people_list.pop(user_name, None)
        else:
            people_list[user_name] = command_clean
        message_text = user_name + "\n" + messages_db.get(command_clean, message.text)[1]
        bot.send_message(message.chat.id, message_text, reply_markup=online_buttons())


@bot.message_handler(commands=["info"])
def send_info(message: telebot.types.Message):
    response = f"Chat ID: {message.chat.id}\n"
    response += f"Active chats: {allow_chats}\n"
    response += f"Bot here is {['Ina', 'A'][str(message.chat.id) in allow_chats]}ctive"
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=["кнопки", "buttons"])
def send_status(message):
    if not str(message.chat.id) in allow_chats:
        return
    global buttons_shown
    if buttons_shown:
        buttons = ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Кнопки прибрано", reply_markup=buttons)
    else:
        buttons = ReplyKeyboardMarkup(row_width=3)
        buttons_list = []
        for key, name in messages_db.items():
            buttons_list.append(KeyboardButton("/" + key))
        buttons.add(*buttons_list)
        bot.send_message(message.chat.id, "Кнопки показано", reply_markup=buttons)
    buttons_shown = not buttons_shown


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: telebot.types.CallbackQuery):
    if not str(call.message.chat.id) in allow_chats:
        return
    if call.data[:-1] == 'cb_group':
        target_category = int(call.data[-1])
        members_text = status_groups[target_category] + ": \n"
        members_list = ""
        for member_name, status in people_list.items():
            category, full_status = messages_db[status]
            if category == target_category:
                members_list += member_name + ": " + full_status + " \n"
        if not len(members_list):
            members_list = "Нікого"
        bot.answer_callback_query(call.id, members_text + members_list, True)


bot.polling(none_stop=True)

