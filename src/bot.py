#!/usr/bin/python

# from pprint import pprint # better error printing in msg-dics 
import telepot as tp
import configparser
from src.vp import Vp

class Archebot(tp.Bot):
    """
    runs a bot wich can read the vertretungsplan and other things
    needed files: configuration file, answer file
    """

    # Initialization functions
    def __init__ (self, configfile = "autoexec.cfg", *args, **kwargs):
        """
        initialize variables, set the token, curoff and the Bot
        """
        # Parse the config file
        self.__config = configparser.ConfigParser()
        self.__config.read(configfile)
        print(self.__config['telegram']['token'])
        super().__init__(self.__config['telegram']['token'], *args, *kwargs)

        # read the telegram config
        self.__token   = self.__config['telegram']['token']
        self.__logfile = self.__config['telegram']['logfile']

        # Set the telegram-Bot variable
        self.__bot = tp.Bot(self.__token)

        # Init the vp class
        self.__initvp()

        
    def __initvp (self):
        """
        inits the vp 
        """
        website  = self.__config['vp']['website']
        sid      = self.__config['vp']['sid']
        database = self.__config['vp']['database']
        vpdate   = self.__config['vp']['vpdate']
        language = self.__config['vp']['language']
        if "" in [website, sid, database, vpdate, language]:
            print("Error: One of the vp conf values is empty")

        self.__vp = Vp(website, vpdate, sid, database, language)


    def handle(self, msg):
        """
        handle the received messages
        core of the script
        """
        text = msg[u'message'][u'text'] # message the bot received
        u_id = msg[u'message'][u'from'][u'id'] # user-id = chat-id
        print (u_id, msg[u'message'][u'from'][u'username'])

        command = text.split(" ", 1)
        if len(command) == 1:
            command.append("")

        if command[0][0] == "/":
            command[0] = command[0].replace("/", 1)

        if command[0] == "help":
            self.__sendHelp(u_id)
        elif command[0] == "vp":
            self.__showVp(u_id)
        elif command[0] == "info":
            self.__showInfo(u_id)
        elif command[0] == "url":
            self.__setURL(u_id, command[1])
        elif command[0] == "add":
            self.__addSubj(u_id, command[1])
        elif command[0] == "del":
            self.__delSubj(u_id, command[1])
        elif command[0] == "delme":
            self.__delUser(u_id, command[1])
        else:
            self.__bot.sendMessage(chat_id=u_id, text = "Hi, " + (msg[u'message'][u'from'][u'first_name'] if msg[u'message'][u'from'][u'first_name'] != "" else msg[u'message'][u'from'][u'username']))

    def __sendHelp(self, u_id):
        response = self.__vp.getUserHelp(u_id)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __showVp (self, u_id):
        """
        pre:  u_id is valid telegram user id
        post: current vertretungsplan is sent to u_id user
        """
        response = self.__vp.getUserStatus(u_id)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __showInfo (self, u_id):
        """
        pre:  u_id is valid telegram user id
        post: registered courses are sent to u_id user
              if user not registered error msg is sent
        """
        response = self.__vp.getUserStatus(u_id)
        self.__bot.sendInfo(chat_id = u_id, text = response)

    def __setURL (self, u_id, url):
        """
        pre:  msg is message sent by user in valid telepot message format
        post: sid of the user is set and if did not happen before added to database
        """
        response = self.__vp.checkUser(u_id, url)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __addSubj (self, u_id, subjects):
        """
        pre:  msg is message sent by user in valid telepot message format
        post: subjects are added to our database
        """
        response = self.__vp.setUserSubjects(u_id, subjects)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __delSubj (self, u_id, subjects):
        """
        pre:  msg is message sent by user in valid telepot message format
        post: comma separated subjects are deleted from our database
        """
        response = self.__vp.delUserSubjects(u_id, subjects)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __resetSubj (self, u_id):
        """
        pre:  u_id is valid telegram user id
        post: all subjects are deleted from our database
        """
        response = self.__vp.resetUserSubjects(u_id)
        self.__bot.sendMessage(chat_id = u_id, text = response)

    def __delUser (self, u_id, command):
        """
        pre:  u_id is valid telegram user id
        post: confirmation is asked by user, command for real deletion is sent
        """
        response = self.__vp.delUser(u_id, command)
        self.__bot.sendMessage(chat_id = u_id, text = response)

