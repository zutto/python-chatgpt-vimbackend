#!/usr/bin/env python3.11
import json
import sys
import os
from revChatGPT.V1 import AsyncChatbot, Chatbot
import asyncio
import time
import signal 
import uuid

Sessions = []
convo = None

role = ""

class Session:
    _type = None
    _convo = None
    _title_set = False
    _bot = None
    _role = None
    def __init__(self):
        pass


    def Bot(self):
        if self._bot is not None:
            return self._bot

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

        #self._bot = AsyncChatbot(config = config,
        self._bot = Chatbot(config = config,
                base_url=os.environ.get("CHATGPT_BASE_URL")
        )
        return self._bot



    def Type(self, value=None):
        if value is None:
            return self._type
        else:
            self._type = value
            return value

    def Name(self):
        return "{type}-{convo}".format(type=self._type, convo=self._convo)
   
    def Role(self, value = None):
        if value is not None:
            self._role = value
        
        if self._role is None:
            return ""
        return self._role
            
    def Title(self):
        if not self._title_set and self.Convo() is not None:
            self._title_set = True
            self.Bot().change_title(self.Convo(), self.Name())
        return

    def Delete(self):
        if self.Convo() is not None:
            self.Bot().delete_conversation(self.Convo())
            self._convo = None
            self._type = None
            self._title_set = False
            self._Bot = None

    def Convo(self, value=None):
        if value is not None:
            self._convo = value
        return self._convo

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




def query(msg, encoder, convo=None, model: str = "", session: Session = None):
    existing=""
    if session is not None:
        #async for message in session.Bot().ask(msg, model=model, conversation_id=session.Convo()):
        for message in session.Bot().ask(msg, model=model, conversation_id=session.Convo()):
            if session.Convo() is None and 'conversation_id' in message:
                session.Convo(message['conversation_id'])
            encoder.write_json({'eof':False, 'error':'', 'text': message["message"][len(existing):]})
            existing=message["message"]
        #print(encoder.write_json({'eof': True, 'error': '', 'text':''}))
        encoder.write_json({'eof': True, 'error': '', 'text':''})
        return session.Convo()
    else:
        return convo
    
"""
    existing=""
    async for message in bot.ask(msg, model=model):
        if convo is None and 'conversation_id' in message:
            convo = message['conversation_id']
        encoder.write_json({'eof':False, 'error':'', 'text': message["message"][len(existing):]})
        existing=message["message"]

    print(encoder.write_json({'eof': True, 'error': '', 'text':''}))
    return convo
"""
decoder = JSONInputReader(sys.stdin)
encoder = JSONOutputWriter(sys.stdout)

terminate = False
def exit_handler(signum=None, frame=None):
    print("deleting convos")
    global terminate
    terminate = True
    for session in Sessions:
        session.Delete()
    
    sys.exit()

signal.signal(signal.SIGTERM, exit_handler)


def main():
    role=""
    convo=""
    while not terminate:
        try:
            data = decoder.read_json()
        except KeyboardInterrupt:
            exit_handler(None, None)
            """
            print("deleting conversation")        
            if convo is not None:
                asyncio.run(bot.delete_conversation(convo))
            print("done")
            sys.exit()
            """
            break

        except json.JSONDecodeError:
            continue

        model = ""
        if data is None:
            continue
        systemrole = ""
        
        cc = "chat"
        if 'session' in data:
            cc = data["session"]

        _session = None
        for session in Sessions:
            if session.Type() == cc:
                _session = session

        if _session is None:
            _session = Session()
            _session.Type(cc)
            _session._bot = None
            Sessions.append(_session)


        if 'reset' in data:
            if len(data['reset']) > 0:
                _session.Delete()
                _session._convo = None #hack
                continue
                


        if 'role' in data:
            systemrole = data["role"]
        text = data["text"]
        if 'model' in data:
            model = data["model"]
        if _session.Role() != systemrole:
            _session.Role(systemrole)
            query(f"{systemrole}\n{text}", encoder, convo=convo, model=model, session=_session)
            _session.Title()
            #await asyncio.run(query(f"{systemrole}\n{text}", bot, encoder, convo=convo, model=model, session=_session))
            role = systemrole
        else:
            #await asyncio.run(query(f"{text}", bot, encoder, convo=convo, model=model, session=_session))
            query(f"{text}", encoder, convo=convo, model=model, session=_session)
            _session.Title()
        time.sleep(0.01)


main()

