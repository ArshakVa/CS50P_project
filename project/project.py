from telebot import TeleBot, types

from ollama import Client
from ddgs import DDGS
from dotenv import load_dotenv
import os

import sqlite3

# ================= Setup =================

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8548104837:AAHWoUpVRP8PjN-_xb2i9dPd6jocNLlYeH0")
bot = TeleBot(token=TOKEN)

connection = sqlite3.connect('gang.db', check_same_thread=False)
cursor = connection.cursor()

# ================= Global Values =================

language = 'English'

user_selections = []
all_expenses = []
current_expense = {}

# ================= Running The Bot =================

def main():
    """
    Start the bot and setup handlers.
    """
    setup_handlers()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

# ================= Handlers =================

def setup_handlers():
    bot.message_handler(commands=['start'])(starter)
    bot.message_handler(commands=['search'])(searcher)
    bot.message_handler(commands=['mammad'])(start_process)
    bot.message_handler(commands=['help'])(help)
    bot.callback_query_handler(func=lambda call: True)(callback_query)

def starter(message):
    """
    Send language selection inline keyboard.
    message -> messeage chat
    -> keyboard of language selection
    """
    bot.send_message(
        message.chat.id,
        'Choose a language:          :زبان را انتخاب کن',
        reply_markup=main_keyboard()
    )

# ================= Help =================

def help(message):
    """
    Provides a guide on how to use the bot's features.
    """
    help_text = (
        "🤖 *Bot Guide:*\n\n"
        "1. **/start**: Change your language settings.\n"
        "2. **/search**: Ask me anything! I will search the web and translate them into your chosen language.\n"
        "3. **/mammad**: Start the 'Gang' Expense Manager. I'll help you calculate "
        "who owes whom after a group outing.\n"
        "   - Select participants.\n"
        "   - Add expenses (Group or Individual).\n"
        "   - Get a final settlement plan.\n\n"
    )

    final_text = translate(help_text, 'English', language)
    
    bot.send_message(
        message.chat.id, 
        final_text, 
        parse_mode="Markdown"
    )
# ================= Translation =================

def searcher(message):
    """
    Search using LLM.
    message -> messeage chat
    -> sending message sent to process_LLM()
    """
    msg = bot.send_message(message.chat.id, translate('Tell me what you want to know: ', 'English', language))
    bot.register_next_step_handler(msg, LLM, language)



def handle_language_selection(call):
    global language
    if call.data == 'en_button':
        language = 'English'
        bot.answer_callback_query(call.id, "English")
        bot.edit_message_text(f"Language set to <b>English</b>", call.message.chat.id, call.message.message_id, reply_markup=None, parse_mode="HTML")
        bot.send_message(call.message.chat.id, 'Hello👋. How may I help you today?')
    else:
        language = 'Farsi'
        bot.answer_callback_query(call.id, "Farsi")
        bot.edit_message_text(f"زبان <b>فارسی</b> انتخاب شد", call.message.chat.id, call.message.message_id, reply_markup=None, parse_mode="HTML")
        bot.send_message(call.message.chat.id, 'سلام👋. امروز چه کمکی ازم ساختس؟')
        

def translate(text, from_language= 'English', to_language= 'Farsi'):
    if from_language == to_language:
        return text
    load_dotenv()
    API_KEY = os.getenv("OLLAMA_API_KEY")
    TranslatorModel = os.getenv("OLLAMA_DEEPSEEK_MODEL")

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    response = client.chat(
        model=TranslatorModel,
        messages=[
            {
                "role": "system", 
                "content" : f"You are a professional translator who translates {from_language} to fluent {to_language}. Use natural, clear translation with proper punctuation."
            },
            {
                "role":"user", 
                "content" : f"Translate this text to {to_language}:\n\n{text}"
            }
        ]
    )

    return response.message.content


# ================= LLM Functions =================

def LLM(tel_message, language= 'English'):
    load_dotenv()
    API_KEY = os.getenv("OLLAMA_API_KEY")
    SummarizerModel = os.getenv("OLLAMA_GPT_MODEL")
    TranslatorModel = os.getenv("OLLAMA_DEEPSEEK_MODEL")

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    status = bot.send_message(tel_message.chat.id, f'🔎 searching...')
    ## Search
    def search(topic, num_results= 3):
        results = []

        with DDGS() as ddgs:
            for out in ddgs.text(topic, max_results=num_results):
                results.append(f"Title: {out['title']}\nURL: {out['href']}\nSnippet: {out['body']}\n")
                
        bot.edit_message_text("📝 Summarizing...", tel_message.chat.id, status.message_id)
        return "\n".join(results)

    ## Summarize
    def summarize(text):

        response = client.chat(
            model=SummarizerModel,
            messages=[
                {
                    "role":"system", 
                    "content" : "You are a professional summarizer.Summarize text clearly and concisely in fluent English. Limit the summary to no more than 150 words."
                },
                {
                    "role":"user", 
                    "content" : f"Please summarize the following texts, which are all on the same topic:\n\n{text}"
                }
            ]
        )
        
        return response.message.content

    ## Translator
    def translate(english_text):
        bot.edit_message_text("💬 Translating...", tel_message.chat.id, status.message_id)

        response = client.chat(
            model=TranslatorModel,
            messages=[
                {
                    "role": "system", 
                    "content" : "You are a professional translator who translates English to fluent Persian(Farsi). Use natural, clear Farsi with proper punctuation.Limit the translation to no more than 150 words."
                },
                {
                    "role":"user", 
                    "content" : f"Translate this text to Persian:\n\n{english_text}"
                }
            ]
        )

        return response.message.content
    

    topic = tel_message.text

    search_results = search(topic)

    summary = summarize(search_results)
    if language == 'English':
        output = summary
    elif language == 'Farsi':
        output = translate(summary)

    bot.edit_message_text(output, tel_message.chat.id, status.message_id)
    return 


# ================= mammad =================

def main_keyboard():
    """
    create language selection inline keyboard.
    """
    en_button = types.InlineKeyboardButton(text="English", callback_data="en_button")
    fas_button = types.InlineKeyboardButton(text="Farsi", callback_data="far_button")
    markup = types.InlineKeyboardMarkup()
    markup.add(en_button, fas_button)
    return markup


def get_all_members():
    """
    -> all the informations in the database
    """
    cursor.execute("SELECT id, nickname, first_name, last_name FROM gang")
    return cursor.fetchall()

def get_name_by_id(m_id):
    """
    m_id -> id
    -> {(fist name) (last name)} of id
    """
    cursor.execute("SELECT first_name, last_name FROM gang WHERE id=?", (m_id,))
    info = cursor.fetchone()
    return f"{info[0]} {info[1]}" if info else "Unknown"

def create_selection_markup(selected_ids, is_for_all):
    """
    selected_ids -> specified ids as a list
    is_for_all -> using True when for taking all the participants and False for each activity participants
    -> markup
    """
    markup = types.InlineKeyboardMarkup()
    if is_for_all:
        members = get_all_members()
        id_fullname_list = [(str(m[0]), f"{m[2]} {m[3]}") for m in members]
    else:
        id_fullname_list = [(str(m_id), get_name_by_id(m_id)) for m_id in user_selections]

    for m_id, full_name in id_fullname_list:
        status = " ✅" if str(m_id) in selected_ids else ""
        markup.add(types.InlineKeyboardButton(text=f"{full_name}{status}", callback_data=f"toggle_{m_id}"))

    label = "✅ تایید نهایی لیست" if not is_for_all else "📥 ثبت لیست اعضای کل"
    callback = "confirm_participants" if not is_for_all else "final_submit"
    markup.add(types.InlineKeyboardButton(text=label, callback_data=callback))
    return markup

def create_individual_markup(individual_data):
    """
    individual_data -> dictionary of id : share(money the id should pay)
    -> markup for adding the share of individual
    """
    markup = types.InlineKeyboardMarkup()
    total = sum(individual_data.values())
    for m_id in user_selections:
        full_name = get_name_by_id(m_id)
        amount = individual_data.get(str(m_id), 0)
        status = f" 💰 {amount:,}" if amount > 0 else " ➖"
        markup.add(types.InlineKeyboardButton(text=f"{full_name}{status}", callback_data=f"set_indiv_{m_id}"))

    markup.add(types.InlineKeyboardButton(text=f"✅ ثبت (مجموع: {total:,})", callback_data="confirm_individual_total"))
    return markup

def create_payer_markup():
    """
    -> markup for taking the payer
    """
    markup = types.InlineKeyboardMarkup()
    for m_id in user_selections:
        full_name = get_name_by_id(m_id)
        markup.add(types.InlineKeyboardButton(text=f"👤 {full_name}", callback_data=f"set_payer_{m_id}"))
    return markup

def main_menu():
    """
    -> markup for adding or ending new activity
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="➕ اضافه کردن خرج جدید", callback_data="add_spender"))
    markup.add(types.InlineKeyboardButton(text="🔚 اتمام و محاسبه دنگ‌ها", callback_data="calculate_total"))
    return markup

# ================= Callback Query =================

def callback_query(call):
    """
    handle each callback
    """
    global user_selections, current_expense, all_expenses
    chat_id = call.message.chat.id

    # Language Selection
    if call.data in ['en_button', 'far_button']:
        handle_language_selection(call)
        return

    # Expense Handling
    # ================= for all the participants
    if call.data.startswith("toggle_"):
        m_id = call.data.split("_")[1]
        if "حضور دارند" in call.message.text:
            if m_id in user_selections: 
                user_selections.remove(m_id)
            else: 
                user_selections.append(m_id)
            markup = create_selection_markup(user_selections, is_for_all=True)
        else: 
            if 'temp_participants' not in current_expense: 
                current_expense['temp_participants'] = []
            if m_id in current_expense['temp_participants']: 
                current_expense['temp_participants'].remove(m_id)
            else: 
                current_expense['temp_participants'].append(m_id)
            markup = create_selection_markup(current_expense['temp_participants'], is_for_all=False)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    # ================= for ending adding all the participants
    elif call.data == "final_submit":
        if not user_selections:
            bot.answer_callback_query(call.id, "❌ کسی انتخاب نشده!")
            return
        bot.edit_message_text(f"📍 حاضرین ({len(user_selections)} نفر) تایید شدند.", chat_id, call.message.message_id)
        bot.send_message(chat_id, "حالا خرج‌ها را وارد کنید:", reply_markup=main_menu())
      
    # ================= creating an expense profile  
    elif call.data == "add_spender":
        current_expense = {'description': '', 'type': '', 'amount': 0, 'individual_amounts': {}, 'temp_participants': []}
        msg = bot.send_message(chat_id, "📝 بابت چیه؟ (مثلاً رستوران)")
        bot.register_next_step_handler(msg, get_description)
        
    # ================= updating the profile for group activities  
    elif call.data == "type_group":
        current_expense['type'] = 'group'
        msg = bot.send_message(chat_id, "💰 مبلغ کل هزینه:")
        bot.register_next_step_handler(msg, get_amount_group)

    # ================= updating the profile for individual activities 
    elif call.data == "type_individual":
        current_expense['type'] = 'individual'
        bot.send_message(chat_id, "سهم هر نفر را وارد کنید (مبلغ فاکتور):", reply_markup=create_individual_markup({}))
        
    # ================= panel for adding the share of each individuel
    elif call.data.startswith("set_indiv_"):
        u_id = call.data.split("_")[2]
        q_msg = bot.send_message(chat_id, f"سهم {get_name_by_id(u_id)}:")
        bot.register_next_step_handler(q_msg, save_individual_amount, u_id, call.message.message_id, q_msg.message_id)
        
    # ================= confirming total
    elif call.data == "confirm_individual_total":
        current_expense['amount'] = sum(current_expense['individual_amounts'].values())
        bot.send_message(chat_id, "👤 چه کسی پرداخت کرده؟", reply_markup=create_payer_markup())
        
    # ================= setting the payer   
    elif call.data.startswith("set_payer_"):
        current_expense['payer_id'] = call.data.split("_")[2]
        if current_expense['type'] == 'group':
            bot.send_message(chat_id, f"چه کسانی در {current_expense['description']} سهم دارند؟", reply_markup=create_selection_markup([], False))

        else:
            current_expense['participants'] = list(current_expense['individual_amounts'].keys())
            all_expenses.append(current_expense.copy())
            bot.send_message(chat_id, f"✅ هزینه '{current_expense['description']}' ثبت شد.", reply_markup=main_menu())
            
    # ================= taking the current activity participants       
    elif call.data == "confirm_participants":
        if not current_expense.get('temp_participants'):
            bot.answer_callback_query(call.id, "❌ حداقل یک نفر را انتخاب کنید")
            return
        current_expense['participants'] = list(current_expense['temp_participants'])
        all_expenses.append(current_expense.copy())
        bot.send_message(chat_id, f"✅ هزینه '{current_expense['description']}' ثبت شد.", reply_markup=main_menu())
        
    # ================= final
    elif call.data == "calculate_total":
        show_final_results(chat_id)
        

# ================= mammad Command =================

def start_process(message):
    """Start the expense process."""
    global user_selections, all_expenses
    user_selections, all_expenses = [], []
    bot.send_message(message.chat.id, "چه کسانی حضور دارند؟ 👥", reply_markup=create_selection_markup([], True))


def get_description(message):
    current_expense['description'] = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👥 جمعی (تقسیم مساوی)", callback_data="type_group"),
               types.InlineKeyboardButton("👤 تکی (هرکس سهم خودش)", callback_data="type_individual"))
    bot.send_message(message.chat.id, "نوع تقسیم هزینه:", reply_markup=markup)
    
def get_amount_group(message):
    current_expense['amount'] = int(message.text)
    bot.send_message(message.chat.id, "👤 چه کسی پرداخت کرده؟", reply_markup=create_payer_markup())

# deleting 
def save_individual_amount(message, u_id, list_msg_id, q_id):
    try: 
        bot.delete_message(message.chat.id, q_id)
    except: 
        pass
    try: 
        bot.delete_message(message.chat.id, message.message_id)
    except: 
        pass
    
    current_expense['individual_amounts'][u_id] = int(message.text)
    bot.edit_message_reply_markup(message.chat.id, list_msg_id, reply_markup=create_individual_markup(current_expense['individual_amounts']))

# ================= Final Balances =================

def calculate_final_balances(selected_ids, expenses):
    """
    selected_ids -> present ids
    expenses -> list of dictionaries of expences info
    """
    balances = {get_name_by_id(m_id): 0 for m_id in selected_ids}
    report = "📊 **جزئیات هزینه‌ها:**\n"
    
    for exp in expenses:
        payer_name = get_name_by_id(exp['payer_id'])
        net_total = exp['amount']

        balances[payer_name] += net_total
        
        if exp['type'] == 'group':
            p_ids = exp['participants']
            share_per_person = net_total / len(p_ids)
            for p_id in p_ids:
                balances[get_name_by_id(p_id)] -= share_per_person
            report += f"🔹 {exp['description']}: {net_total:,} (پرداخت: {payer_name})\n"
        
        else:
            total = exp['amount']
            indiv_list = []
            for u_id, u_amt in exp['individual_amounts'].items():
                name = get_name_by_id(u_id)
                balances[name] -= u_amt

                indiv_list.append(f"{name}: {int(u_amt):,}")
            report += f"🔸 {exp['description']}: {net_total:,} (پرداخت: {payer_name})\n   [ { ' | '.join(indiv_list) } ]\n"

    report += "\n💰 **وضعیت نهایی (طلب/بدهی):**\n"
    for p, b in balances.items():
        emoji = "🟢 " if b > 1 else "🔴 " if b < -1 else "⚪️ "
        report += f"{emoji}{p}: {abs(int(b)):,}\n"

    debtors = [{'name': p, 'amount': abs(b)} for p, b in balances.items() if b < -1]
    creditors = [{'name': p, 'amount': b} for p, b in balances.items() if b > 1]
    
    plan = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        settle = min(debtors[i]['amount'], creditors[j]['amount'])
        plan.append(f"👤 {debtors[i]['name']} ➡️ {int(settle):,} تومان ➡️ {creditors[j]['name']}") # persian difference!!!
        debtors[i]['amount'] -= settle
        creditors[j]['amount'] -= settle
        if debtors[i]['amount'] <= 1: i += 1
        if creditors[j]['amount'] <= 1: j += 1

    return balances, report, plan

def show_final_results(chat_id):
    balances, report, plan = calculate_final_balances(user_selections, all_expenses)
    bot.send_message(chat_id, report + "\n🏁 **نحوه تسویه حساب:**\n" + ("\n".join(plan) if plan else "همه حساب‌ها صاف است! ✅"), parse_mode="Markdown")


# ================= Entry Point =================

if __name__ == "__main__":
    main()
