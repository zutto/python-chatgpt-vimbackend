#!/usr/bin/env python3.11
import subprocess
import json
import os
import sys
import signal

class JSONInputReader:
    def __init__(self, file):
        self.file = file
        self.decoder = json.JSONDecoder()

    def read_json(self):
        try:
            line = self.file.readline().decode("utf-8").rstrip()
            if line:
                return self.decoder.decode(line)
        except json.JSONDecodeError:
            
            print(f"decode error\n{line}")
            pass
        except Exception as e:
            print(e)
            pass
        return None

class JSONOutputWriter:
    def __init__(self, file):
        self.file = file
        self.encoder = json.JSONEncoder()

    def write_json(self, data):
        if len(data) > 1:
            json_data = {
                "role": os.getenv("OPENAI_TERM_ROLE", "You are a expert of all terminal emulators. You always great good commands and tips for the user while keeping output to minimum."),
                "model": "gpt3.5",
                "text": data,
                "session": "bash"
            }
            self.file.write(self.encoder.encode(json_data).encode("utf-8") + "\n".encode("utf-8"))
            self.file.flush()


def process_json_output(input):
    if "eof" in input:
        if input["eof"] and input["eof"] == True:
            return False # break
    
    if "text" in input:
        print(input["text"], end="")
    return True


chatgpt_process = subprocess.Popen(["/usr/bin/env", "chatgpt"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=os.environ.copy())
reader = JSONInputReader(chatgpt_process.stdout)
writer = JSONOutputWriter(chatgpt_process.stdin)

def exit_handler(signum=None, frame=None):
    chatgpt_process.send_signal(signal.SIGTERM)
    chatgpt_process.wait()
    sys.exit()







input_data = " ".join(sys.argv[1:]) if sys.stdin.isatty() else sys.stdin.read().strip()
writer.write_json(input_data)

while True:
    try:
        line = reader.read_json()
    except KeyboardInterrupt:
            exit_handler(None, None)
 

    if not line:
        continue
    try:
        if not process_json_output(line):
            break
    except Exception as e:
        print(e)
        break

chatgpt_process.send_signal(signal.SIGTERM)
chatgpt_process.wait()
