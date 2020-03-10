# Bad weather sms sender
Service for sending SMSes.\
Project based on [Quart](https://gitlab.com/pgjones/quart) and uses [Trio](https://github.com/python-trio/trio) async implementation.\
For sending messages uses [SMSc](http://smsc.ru).
# How to install
Python version required: 3.7+
1. Recomended use venv or virtualenv for better isolation.\
   Venv setup example: \
   `python3 -m venv myenv`\
   `source myenv/bin/activate`
2. Install requirements: \
   `pip3 install -r requirements.txt` (alternatively try add `sudo` before command)

# How to launch
1) Add to your environment some variables:
   `SMS_LOGIN` - SMSc api login\
   `SMS_PASS` - SMSc api password\
   `REDIS_HOST` - Redis host\
   `REDIS_PORT` - Redis port\
   `REDIS_PASS` - Redis password\
   `DEBUG_SENDER` - Set if you want see debug messages
   
2) Run `python3 server.py` and open on your browser `127.0.0.1:5000`

# Project Goals
The code is written for educational purposes. Training course for web-developers - [DVMN.org](https://dvmn.org)
