#!/opt/homebrew/bin/python3.11
import json
import sys
import os
from revChatGPT.V1 import AsyncChatbot
import uuid
import asyncio
import time
import signal 

UUID = str(uuid.uuid4())
convo = None

role = ""
bot = AsyncChatbot(config={
        "access_token": os.environ.get("CHATGPT_API_KEY"),
        "paid": True
        },
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
            #self.file.write(self.encoder.encode(data)) #still dont understand why this doesnt work with vim
            print(self.encoder.encode(data))
            self.file.flush()




async def query(msg, bot, encoder, convo=None):
    
    existing=""
    async for message in bot.ask(msg):
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
        # Read in the JSON input from stdin
        # Parse the JSON
        data = decoder.read_json()
        # Access the "Text" and "Systemrole" values
    except KeyboardInterrupt:
        print("deleting conversation")        
        if convo is not None:
            asyncio.run(bot.delete_conversation(convo))
        print("done")
        sys.exit()
        break

    # Exit gracefully if the user hits Ctrl+C
    except json.JSONDecodeError:
        continue

    if data is None:
        continue
    systemrole = data["role"]
    text = data["text"]

    if role != systemrole:
        convo=asyncio.run(query(f"{systemrole}\n{text}", bot, encoder, convo=convo))
        role = systemrole
    else:
        convo=asyncio.run(query(f"{text}", bot, encoder, convo=convo))
    time.sleep(0.01)


