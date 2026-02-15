# Gholam Telegram Bot
#### Video Demo: https://youtu.be/31n3yn0ObyE?si=ZCwPV0XnQT6674Up

#### Description:
At first, I needed the bot itself. BotFather is the official Telegram bot that allows you to create new bots. It lets you give your bot a name and username and provides a token to access its API. Now we have a bot that can run freely, but its functions won’t work yet. To enable them, we need to define the bot’s abilities, which is possible using the token provided by BotFather and the TeleBot library in Python.

After a lot of trial and error, I learned how to implement basic bot functionalities: reading messages, sending messages, replying to messages, and much more. Once I understood how to write these functions, I realized that I needed some information from users: first name, last name, nickname, and card number.

To collect this information, I could run gang.py on a local machine, but I decided to run it on a server so that all my friends could provide their information directly without me needing to run the code on my computer. After gathering the required information, I set up a database to store it. While MySQL would have required setting up an account and server, SQLite was much simpler for my needs—it just creates a database file.

With all the necessary information available and the TeleBot library working, it was showtime. For the search feature, I created an inline keyboard to select the language. Using a translation function and an Ollama model, the bot sends welcome messages. Now users can run /search, type their query, and the bot will search using another Ollama model, summarize the results, and, if needed, translate them into the selected language.

The main functionality, however, was more complex. Sending /mammad starts the expense tracking workflow. This requires multiple inline buttons, each with a specific function. First, we specify which gang members are participating in the activity. Then, we provide details about the activity:

Type of activity:
Group -> when everyone shares equally.
Individual -> when each person has their own share.
Participants: not all gang members are always involved
Payer: the person who paid

After collecting all this information, the bot calculates each person’s share and generates an optimized settlement plan with minimal transactions.

Finally, both the Ollama search functionality and the expense calculation can be tested using test_project.py.

Writing such functionality may seem easy, but for someone like me, who had no prior experience and learned everything in just three weeks, it was a fantastic challenge. There were many problems along the way. For example, when VPNs didn’t work, I had to imagine the output of each function because I couldn’t test them directly. Some servers on Ollama were also banned, causing additional delays. The code itself had many challenges: I had to write complex interactive inline keyboards, handle multiple names and calculations, and ensure all interactions worked smoothly. At first, I realized my code wasn’t testable, but after a lot of effort, everything works properly.
