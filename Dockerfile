FROM ubuntu
RUN apt update
RUN apt install git -y
RUN apt install python3 python3-pip -y
RUN pip install --upgrade pip
RUN git clone https://github.com/ww-insight/simple_gpt_bot.git
RUN pip install -r simple_gpt_bot/requirements.txt
ENV OPENAI_API_KEY ???
ENV TELEGRAM_BOT_TOKEN ???
ENTRYPOINT python3 simple_gpt_bot/main.py