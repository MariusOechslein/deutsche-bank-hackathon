import datetime
import os
import csv

class Chat:
    def __init__(self, user,first_name,id):
        self.user = user
        self.first_name = first_name
        self.id = id
        self.chat_history = []
        self.gpt_history = []
        self.name_user_id = f'{self.first_name}_{self.id}'
        default_gpt_message = {"role": "system",
                               "content":"You are a helpful assistant that help users achieve their financial targets and advise them on proper management of their finance.",
                               "context": None,
                               "timestamp": datetime.datetime.now(),
                               "chat_id": None,
                               "message_id": None
                               }
        self.gpt_history.append(default_gpt_message)

    def reset_gpt_conversation_history(self):
        self.gpt_history = []

    def add_message(self, role, content,chat_id,message_id, context=None, gpt_history=False):
        timestamp = datetime.datetime.now()
        if role not in ['assistant','system']:
            role = 'user'
        message = {
            "role": role,
            "content": content,
            "context": context,
            "timestamp": timestamp,
            "chat_id": chat_id,
            "message_id": message_id
        }
        if gpt_history:
            self.gpt_history.append(message)
        self.chat_history.append(message)
        self.save_to_text(message)

    def save_prompts(self,question,context,answer,evaluation,comment,mid_question,cid_question,mid_answer,cid_answer,name_user,user_name):
        prompt = {
            "question":question,
            "context":context,
            "answer":answer,
            "evaluation":evaluation,
            "comment":comment,
            "mid_question":mid_question,
            "cid_question":cid_question,
            "mid_answer":mid_answer,
            "cid_answer":cid_answer,
            "name_user":name_user,
            "user_name":user_name
        }
        filename = f'conversations/chatgpt_prompts.csv'
        # Check if the CSV file exists
        file_exists = os.path.isfile(filename)
        
        # Open the CSV file in append mode
        with open(filename, 'a', newline='') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.DictWriter(csvfile, fieldnames=prompt.keys())
            
            # If the file doesn't exist, write the header row
            if not file_exists:
                csv_writer.writeheader()
            
            # Write the data as a new row
            csv_writer.writerow(prompt)

    def edit_prompt_eval(self,cid_answer,mid_answer,value,column):
        # Open the CSV file in read mode
        filename = f'conversations/chatgpt_prompts.csv'
        with open(filename, 'r', newline='') as csvfile:
            # Create a CSV reader object
            csv_reader = csv.DictReader(csvfile)
            
            # Create a list to store rows
            rows = []
            # Iterate over each row in the CSV file
            for row in csv_reader:
                # Check if the values in column1 and column2 match the specified values
                if row['cid_answer'] == cid_answer and row['mid_answer'] == mid_answer:
                    # Update the value in the specified column
                    print('Found match')
                    row[column] = value
                
                # Add the updated row to the list
                rows.append(row)
    
        # Write the updated rows back to the CSV file
        with open(filename, 'w', newline='') as csvfile:
            # Get the fieldnames from the first row of the CSV file
            fieldnames = rows[0].keys()
            
            # Create a CSV writer object
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write the header row
            csv_writer.writeheader()
            
            # Write the updated rows
            csv_writer.writerows(rows)

    def save_to_text(self, message):
        filename = f"conversations/{self.name_user_id}_conversation_history.txt"
        sender = message['role'] if message['role'] != "assistant" else "assistant"
        line = f"[{message['timestamp']}] {sender}: {message['content']}\n"
        with open(filename, mode='a', encoding='utf-8') as file:
            file.write(line)

    def get_last_user_message(self):
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message
        return None

    def get_last_assistant_message(self):
        for message in reversed(self.messages):
            if message["role"] == "assistant":
                return message
        return None

    def get_message_by_id(self, message_id):
        for message in self.messages:
            if message["id"] == message_id:
                return message
        return None
    
    def __str__(self):
        # return "username "+self.user + "first_name "+ self.first_name
        return f"Chat(user={self.user}, first_name={self.first_name}, history={self.chat_history}, gpt_history={self.gpt_history})"

class ChatManager:
    def __init__(self):
        self.chats = {}

    def get_chat(self, user,first_name,id):
        if user not in self.chats:
            self.chats[user] = Chat(user,first_name,id)
        return self.chats[user]