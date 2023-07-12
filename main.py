#!/usr/bin/python3.11
import json
import sys
import os
from revChatGPT.V1 import AsyncChatbot
import asyncio
import time
import signal 

convo = None

role = ""
config = {
        "email": os.getenv("OPENAI_USER", None),
        "password":  os.getenv("OPENAI_PASSWORD", None),
        "access_token": os.getenv("CHATGPT_API_KEY", None),
}



if not os.environ.get("CHATGPT_API_KEY") or len(os.environ.get("CHATGPT_API_KEY")) < 1:
    config.pop("access_token")
if not os.environ.get("OPENAI_USER") or not os.environ.get("OPENAI_PASSWORD"):
    config.pop("email")
    config.pop("password")

if os.environ.get("OPENAI_PAID"):
    config["paid"] = True

bot = AsyncChatbot(config = config,
        conversation_id=convo or None,
        base_url=os.environ.get("CHATGPT_BASE_URL")
)




class JSONInputReader:
    def __init__(self, file):
        self.file = file
        self.decoder = json.JSONDecoder()

    def read_json(self):
        try:
            line = self.file.buffer.readline().rstrip()
            if line:
                return self.decoder.decode(line.decode('utf-8'))
        except json.JSONDecodeError:
            pass
        except Exception as e:
            pass
        return None

class JSONOutputWriter:
    def __init__(self, file):
        self.file = file
        self.encoder = json.JSONEncoder()

    def write_json(self, data):
        if len(data) > 1:
            print(self.encoder.encode(data))
            self.file.flush()




async def query(msg, bot, encoder, convo=None, model: str = ""):
    
    existing=""
    async for message in bot.ask(msg, model=model):
        if convo is None and 'conversation_id' in message:
            convo = message['conversation_id']
        encoder.write_json({'eof':False, 'error':'', 'text': message["message"][len(existing):]})
        existing=message["message"]

    print(encoder.write_json({'eof': True, 'error': '', 'text':''}))
    return convo

decoder = JSONInputReader(sys.stdin)
encoder = JSONOutputWriter(sys.stdout)


def exit_handler(signum, frame):
    print("deleting conversation")        
    if convo is not None:
        asyncio.run(bot.delete_conversation(convo))
    print("done")
    sys.exit()

signal.signal(signal.SIGTERM, exit_handler)

while True:
    try:
        data = decoder.read_json()
    except KeyboardInterrupt:
        print("deleting conversation")        
        if convo is not None:
            asyncio.run(bot.delete_conversation(convo))
        print("done")
        sys.exit()
        break

    except json.JSONDecodeError:
        continue

    model = ""
    if data is None:
        continue
    systemrole = ""
    if 'role' in data:
        systemrole = data["role"]
    text = data["text"]
    if 'model' in data:
        model = data["model"]
    if role != systemrole:
        convo=asyncio.run(query(f"{systemrole}\n{text}", bot, encoder, convo=convoi, model=model))
        role = systemrole
    else:
        convo=asyncio.run(query(f"{text}", bot, encoder, convo=convo, model=model))
    time.sleep(0.01)


