

PYTHON = python3.11
CHATGPT_TARGET = chatgpt
GPT_TARGET = help
BIN_DIR = /usr/local/bin/

all: chatgpt gpt
deps: requirements

requirements: 
	$(PYTHON) -m pip install -r requirements.txt

chatgpt:
	cp chatgpt.py $(BIN_DIR)$(CHATGPT_TARGET)
	chmod u+x $(BIN_DIR)$(CHATGPT_TARGET)


gpt:
	cp gpt.py $(BIN_DIR)$(GPT_TARGET)
	chmod u+x $(BIN_DIR)$(GPT_TARGET)
	

install: all

clean:
	rm $(BIN_DIR)$(CHATGPT_TARGET)	
	rm $(BIN_DIR)$(GPT_TARGET)	
