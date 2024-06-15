# Winning the Deutsche Bank Hackathon

This is the repo for the Deutsche Bank Hackathon in collaboration with THWS Master AI in Würzburg.
Also Nebius AI was kind enough to sponsor V100 GPUs for the day.

## Problem statement II: AI Financial Assistant

### Description
People often struggle with managing their finances and lack access to affordable personalised financial advice. There is a need for a tool that is able to answer both common and specific financial questions to help improve financial literacy and achieve financial targets.

### Details
Develop a tool to help users achieve their financial targets and advise them on proper management of their finance. Tool must notify users that it's not a professional financial adviser and users could follow advises only on their own risk. 

Example features: (These are ideas to inspire your development and do not need to necessarily be implemented)
- Budgeting: offer budgeting strategy, categorize expenses
- Savings goals: set and track savings goals, provide savings tips
- Investment education: types of investment, beginner strategies
- Financial planning: personalised financial plans
- Debt management: personalised debt management plans, minimise interest payments

## Our Solution
Our approach was to build a conversational RAG chatbot that knows about a few popular personal financing tips, that we got from the internet.

### RAG
The RAG (Retrieval Augmented Generation) consists of multiple steps.
1. Relevant data (that the LLM should know about specifically) has to be gathered and processed into a format the LLM can work with well.
2. These documents have to be chunked and embedded into vector-format. For this we used the openai small 3 Embedder.
3. All of these vectors have to be stored in a vector database, along with metadata containing the link the website (for citations).
4. Now when a user prompt comes in, this prompt is also embedded using the same embedder.
5. Then we search in the vector database for the closest embedding match (cosine similarity) to the embedding of the prompt. This is the context the LLM should cite/ answer with.
6. This context is then added to our prompt to the generation LLM (we used LLAMA3). If no context was found, we told LLAMA3 to say it doesn't know.

### Data
We scraped the internet for tips on personal finance, collected them and put them into a nice .txt format that LLMs can work with.
Additionally we always saved the link to the website in the corresponding text file, since we wanted to show the citations to the users.

### Telegram bot
We wanted the application to be easily usable, so we decided for creating a telegram bot for it.
The idea is that you can have a conversation with the telegram bot in the telegram app, which is free and many people already have.

### Hosting
We hosted the backend on the NEBIUS AI Virtual server that was provided for us.
That allowed us to have very quick response times since the powerful GPUs accelarate the embedding model and the generation models noticably.
In our presentation, we showed a QR code to the bot and everyone was able to chat with the telegram bot.


# Code setup

Please download Telegram and use this link to use the telebot: https://t.me/FinancialAsisstant_bot

1. Install all the requirements from the requirements.txt file.
2. Be aware that the API keys in this repo are not valid anymore, so please use your own API keys.
3. Then run the main_chatgpt.py file.
4. Open telegram and start chatting.
