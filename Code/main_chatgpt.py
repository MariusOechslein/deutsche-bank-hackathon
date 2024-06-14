import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import openai
import datetime
import csv
from chat import Chat,ChatManager
from rag_retrieval import retrieve_context
from user_data_base import add_user_to_csv,is_user_allowed,get_allowed_users
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb

#API_KEY = os.getenv('API_KEY')
API_KEY_TG = "7415685370:AAFhBI1fgdVTG5O5KWf-_ShPsPGy67HvEQs"
print(f'API Telegram: ',{API_KEY_TG})
bot = telebot.TeleBot(API_KEY_TG)

API_KEY_CGPT = ""
print(f'API ChatGPT: ',{API_KEY_CGPT})

openai.api_key = API_KEY_CGPT

USER_DB_FILE = 'conversations/users_db.csv'
AUTH_TELEBOT_PWD = 'THWS_baubot123!!'
BOT_NAME = 'AI Finance Assitant'
DIST_THRESHOLD = 0.9

user_send_pwd = []

authorized_users = get_allowed_users(USER_DB_FILE)
print(authorized_users)

# authorized_users = ['rodolfoccr','aaalex42','juli_foti','PabloO_19','moechslein','Kroniker','fpfp2000']


conversation_history = [
    {"role": "system",
     "content": "You are a helpful assistant that help users achieve their financial targets and advise them on proper management of their finance."}
]

client = chromadb.PersistentClient(path="storage")

os.environ["OPENAI_API_KEY"] = 'sk-proj-K6G7rknFnUGcX3yL8DjkT3BlbkFJlnkOGz5AMOOHI8KXlYjf'
EMBEDDING_MODEL = 'text-embedding-3-small'

embedding_function = OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'), model_name=EMBEDDING_MODEL)

col = client.get_or_create_collection("rag_system",embedding_function = embedding_function)

MX_RESULTS = 10

def send_long_message(bot, message, answer, max_length=4000):
    # Split the answer into chunks with a maximum length of max_length
    chunks = [answer[i:i + max_length] for i in range(0, len(answer), max_length)]
    
    # Loop through each chunk and send it as a reply
    for chunk in chunks:
        message_sent = bot.reply_to(message, chunk)
    
    return message_sent

def save_answer_result(username, question, context, answer, evaluation):
    filename = "conversations/prompt_results.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        fieldnames = ['username', 'datetime', 'question', 'context', 'answer', 'evaluation']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'datetime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': username,
            'question': question,
            'context': context,
            'answer': answer,
            'evaluation': evaluation
        })


# Define a function to append a single message to the conversation history file
def update_conversation_to_file(user_name, role, content):
    filename = f"conversations/{user_name}_conversation_history.txt"
    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode, encoding="utf-8") as file:
        if role == "assistant":
            sender = "assistant"
        elif role == "system":
            sender = "system"
        else:
            sender = user_name
        timestamp = datetime.datetime.now().strftime("%y.%m.%d, %H:%M:%S")
        line = f"[{timestamp}] {sender}: {content}\n"
        file.write(line)

user_conversations = {}
chat_manager = ChatManager()

# Define a function to check if a user is authorized
def is_user_authorized(username,user_id):
    if username is None:
        return str(user_id) in authorized_users
    else:
        return username in authorized_users

def add_question(conversation,question):
    chat = {"role": "user", "content": question}

    conversation.append(chat)
    return conversation

def build_context(context):

    context_txt = ''

    # Iterate through the list and format each entry
    for index, entry in enumerate(context, start=1):
        text = entry['text']
        source = entry['metadata']['source']
        context_txt += f"{index}.\n{text}\n\nSource document: {source}\n\n"
    
    return context_txt

def add_question_context(conversation,question,context):

    context_txt = context

    prompt = f"Answer the following question using the context below. If the quesion cannot be answered with the context, say you don't know, if unrelated topic, mention your purpose/goal. Mention which source was used to answer the question.\nQuestion: {question}\n\nContext:\n{context_txt}"

    chat = {"role": "user", "content":prompt}

    conversation.append(chat)

    print(f'Prompt\n{prompt}')
    return conversation

def update_conversation(conversation,response):
    chat = {"role":"assistant", "content":response}
    conversation.append(chat)
    return conversation

def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes ✅", callback_data="cb_yes"),
                               InlineKeyboardButton("No ❌", callback_data="cb_no"))
    return markup

def yes_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Yes ✅",callback_data = 'cb_responded'))
    return markup

def no_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("No ❌",callback_data = 'cb_responded'))
    return markup

# Define a function to ask a question to ChatGPT
def ask_question(conversation,question):
    try:
        conversation = add_question(conversation,question)
        response = openai.chat.completions.create(
            model="gpt-4o",  # Change this to the desired model (e.g., "davinci" or "curie")
            messages=conversation,
            max_tokens=2000  # Adjust the maximum number of tokens for the response
        )
        answer = response.choices[0].message.content
        conversation = update_conversation(conversation,answer)
        return conversation,answer
    
    except Exception as e:
        return str(e)


# Define a function to ask a question to ChatGPT
def ask_question_with_context(conversation,question,context):
    try:
        conversation = add_question_context(conversation,question,context)
        response = openai.chat.completions.create(
            model="gpt-4o",  # Change this to the desired model (e.g., "davinci" or "curie")
            messages=conversation,
            max_tokens=2000  # Adjust the maximum number of tokens for the response
        )
        answer = response.choices[0].message.content
        conversation = update_conversation(conversation,answer)
        return conversation,answer
    
    except Exception as e:
        return str(e)
    
# Define a handler for the /start command
@bot.message_handler(commands=['getaccess'])
def get_access(message):
    global chat_manager
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    user_id = message.chat.id
    user_chat = chat_manager.get_chat(user=user_name,first_name=name_user,id = user_id)
    cid = message.chat.id
    mid = message.message_id
    user_chat.add_message(role = user_name,content = message.text,chat_id = cid, message_id = mid)
    exist_user,allowed_user = is_user_allowed(USER_DB_FILE,telegram_username=user_name,telegram_id=user_id)
    print(f'exist {exist_user} allowed {allowed_user}')

    if allowed_user == 'False':
        message_bot = f'Welcome {name_user} to {BOT_NAME}! You are not allowed to chat, please enter the password to gain access to the bot.'
        user_send_pwd.append(user_id)
    elif exist_user == 'True' and allowed_user == 'True':
        message_bot = f"Welcome {name_user} to {BOT_NAME}! You are already allowed to chat."

    if not exist_user:
        add_user_to_csv(file_path=USER_DB_FILE,username=user_name,id=user_id,name=name_user,allowed=False)

    replied_msg = bot.reply_to(message, message_bot)
    user_chat.add_message(role = 'assistant',content = message_bot,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)

# Define a handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chat_manager
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    cid = message.chat.id
    mid = message.message_id
    user_chat = chat_manager.get_chat(user=user_name,first_name=name_user,id=cid)
    user_chat.add_message(role = user_name,content = message.text,chat_id = cid, message_id = mid)
    message_bot = f"Welcome {message.from_user.first_name} to {BOT_NAME}! Type something to start chatting."
    replied_msg = bot.reply_to(message, message_bot)
    user_chat.add_message(role = 'assistant',content = message_bot,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)

# Define a handler for the /end command
@bot.message_handler(commands=['end'])
def send_end(message):
    global chat_manager
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    cid = message.chat.id
    mid = message.message_id
    user_chat = chat_manager.get_chat(user=user_name,first_name=name_user,id=cid)
    user_chat.add_message(role = user_name,content = message.text,chat_id = cid, message_id = mid)
    message_bot = f"Thank you {message.from_user.first_name} for using the {BOT_NAME}! It was a pleasure helping you."
    replied_msg = bot.reply_to(message, message_bot)
    user_chat.add_message(role = 'assistant',content = message_bot,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)


# Define a handler for the /reset command
@bot.message_handler(commands=['reset'])
def send_reset(message):
    global chat_manager
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    cid = message.chat.id
    mid = message.message_id
    user_chat = chat_manager.get_chat(user=user_name,first_name=name_user,id=cid)
    user_chat.add_message(role = user_name,content = message.text,chat_id = cid, message_id = mid)
    message_bot = f"Resetting your conversation history!"
    replied_msg = bot.reply_to(message, message_bot)
    user_chat.add_message(role = 'assistant',content = message_bot,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)
    user_chat.reset_gpt_conversation_history()

# Define a handler for the /reset command
@bot.message_handler(commands=['cancel'])
def send_cancel(message):
    global chat_manager
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    cid = message.chat.id
    mid = message.message_id
    user_chat = chat_manager.get_chat(user=user_name,first_name=name_user,id=cid)
    user_chat.add_message(role = user_name,content = message.text,chat_id = cid, message_id = mid)
    message_bot = f"Operation canceled!"
    replied_msg = bot.reply_to(message, message_bot)
    user_chat.add_message(role = 'assistant',content = message_bot,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)
    user_send_pwd.remove(cid)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global chat_manager
    cid = call.message.chat.id
    mid = call.message.message_id
    username = call.message.chat.username
    user_name = call.message.from_user.username
    name_user = call.message.from_user.first_name

    user_chat = chat_manager.get_chat(user_name,name_user,id=cid)
    text_answer = 'Your answer was:'
    print(f'Response eval: {call.data} - username: {user_name} name: {name_user} cid: {cid} mid: {mid}')
    if call.data == "cb_yes":
        bot.answer_callback_query(call.id, "Answer is Yes")
        bot.edit_message_text(chat_id=cid, message_id=mid,
                          text=text_answer, reply_markup=yes_markup())
        user_chat.edit_prompt_eval(cid_answer = str(cid),
                                   mid_answer = str(mid - 1),
                                   value = 'good',
                                   column = 'evaluation')
        # bot.delete_message(cid,mid)
        # bot.send_message(cid,"Your answer was:", reply_markup=yes_markup())
    elif call.data == "cb_no":
        bot.answer_callback_query(call.id, "Answer is No")
        bot.edit_message_text(chat_id=cid, message_id=mid,
                          text=text_answer, reply_markup=no_markup())
        user_chat.edit_prompt_eval(cid_answer = str(cid),
                                   mid_answer = str(mid - 1),
                                   value = 'bad',
                                   column = 'evaluation')
    elif call.data == 'cb_responded':
        bot.answer_callback_query(call.id,"Already answered")
        # bot.delete_message(cid,mid)
        # bot.send_message(cid,"Your answer was:", reply_markup=no_markup())

@bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.text == 'Your answer was:')
def reply_msg(message):
    global chat_manager
    cid = message.chat.id
    mid = message.reply_to_message.message_id
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    comment = message.text
    print(f'Your comment was {comment}')
    user_chat = chat_manager.get_chat(user_name,name_user,id = cid)
    user_chat.edit_prompt_eval(cid_answer = str(cid),
                                              mid_answer = str(mid-1),
                                              value = comment,
                                              column = "comment")
    

# Define a handler for regular messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    global user_conversations 
    global chat_manager
    global authorized_users
    # Check if the user is authorized
    user_name = message.from_user.username
    name_user = message.from_user.first_name
    user_id = message.from_user.id
    message_rcvd = message.text
    chat_id = message.chat.id
    message_id = message.message_id
    print(f'id: {user_id} username: {user_name} name: {name_user}')

    user_chat = chat_manager.get_chat(user_name,name_user,id=user_id)

    if user_id in user_send_pwd:
        if message_rcvd == AUTH_TELEBOT_PWD:
            message_to_send = f'Correct password! You can now chat with {BOT_NAME}!'
            add_user_to_csv(file_path=USER_DB_FILE,username=user_name,id=user_id,name=name_user,allowed=True)
            authorized_users = get_allowed_users(USER_DB_FILE)
            user_send_pwd.remove(user_id)

        else:
            message_to_send = f'Incorrect password! Try again! Send /cancel to stop requesting access!'

        replied_msg = bot.reply_to(message, message_to_send)
        user_chat.add_message(role = "assistant",content = message_to_send,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)


    elif is_user_authorized(user_name,user_id):
            
        # Get the message text
        selected_keys = ['role', 'content']
        # Extract dictionaries containing the specified variables
        conversation_history = [{key: d[key] for key in selected_keys} for d in user_chat.gpt_history]

        # gpt_history = {key: user_chat.gpt_history[key] for key in selected_keys}
        input_text = message_rcvd
        user_chat.add_message(role = user_name,content = message_rcvd,chat_id = chat_id,message_id = message_id,gpt_history = True)


        # Check if the input text is too short
        if len(input_text.split()) < 2 or len(input_text) < 5:
            answer = "Your message is too short for me to understand. Please provide more information."
            replied_msg = bot.reply_to(message, answer)
            user_chat.add_message(role = "assistant",content = answer,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = True)
            return
        
        results = retrieve_context(col,message_rcvd,max_results=MX_RESULTS,print_t=False,distance_threshold=DIST_THRESHOLD)
        print(f'RESULTS 1: {results}')

        results = build_context(results)
        print(f'RESULTS 2: {results}')

        # Generate a response using ChatGPT
        # conversation_history,answer = ask_question(conversation_history,input_text)
        conversation_history,answer = ask_question_with_context(conversation_history,input_text,results)

        # Send the response back to the user
        # replied_msg = bot.reply_to(message, answer)
        # Usage
        replied_msg = send_long_message(bot, message, answer)
        answer_mid = replied_msg.id
        answer_cid = replied_msg.chat.id
        quality_resp = bot.send_message(message.chat.id, "Was this a good response?", reply_markup=gen_markup())
        user_chat.add_message(role = "assistant",content = answer,chat_id = answer_cid,message_id = answer_mid,gpt_history = True)
        print(user_chat.gpt_history)
        user_chat.save_prompts(question = input_text,
                               context = results,
                               answer = answer,
                               evaluation = "",
                               comment = "",
                               mid_question = message_id,
                               cid_question = chat_id,
                               mid_answer = answer_mid,
                               cid_answer = answer_cid,
                               name_user = name_user,
                               user_name = user_name)

    else:
        answer = f'Sorry, you are not authorized to interact with this bot. Use command /getaccess to request permission.'
        replied_msg = bot.reply_to(message, answer)
        user_chat.add_message(role = "assistant",content = answer,chat_id = replied_msg.chat.id,message_id = replied_msg.id,gpt_history = False)


# Start the bot
bot.polling()