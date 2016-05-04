#!/usr/bin/python

# from pprint import pprint # better error printing in msg-dics 
import telepot as tp
import vp

class Archebot:

    def __init__ (self):
        """
        initialize variables, set the token, curoff and the Bot
        """
        token = str()
        self.__curoff = 0
        
        conffile = open("avp.cfg","r") # configuration file name: avp.cfg
        conflines = conffile.readlines()
        for line in conflines:
            if line[0] == "#": continue # skip outcommented lines
            if line[0:14] == "telegram_token": # telegram_token has to be first word in line without whitespace
                token = line[16:-2] # characters between the "
                break # don't check other lines -> first appearance is valid
        print(token)
        conffile.close()
        
        self.__bot = tp.Bot(token)
        self.__setcuroff()
        
    def handle(self):
        """
        handle the received messages
        core of the script
        """
        response = self.__bot.getUpdates(offset=self.__curoff)
        if response != []:
            for message in response: self.__response(message)
            self.__setcuroff()
            
    def __setcuroff(self):
        """
        set the current offset of the messages
        important for not to answer the same quest infinitely
        """
        allup = self.__bot.getUpdates()
        if allup == []:
            self.__curoff = 0
        else:
            self.__curoff = allup[-1][u'update_id'] + 1

    def __response (self, msg):
        sent = msg[u'message'][u'text'] # message the bot received
        u_id = msg[u'message'][u'from'][u'id'] # user-id = chat-id
        if sent[0] == "/":
            if sent.split()[0] == "/help":
                self.__bot.sendMessage(chat_id = u_id, text = self.__readans("help"))
            elif sent.split()[0] == "/vp":
                self.__showVp(u_id)
            elif sent.split()[0] == "/info":
                self.__showInfo(u_id)
            elif sent.split()[0] == "/url":
                self.__setURL(u_id)
            elif sent.split()[0] == "/add":
                self.__addUser(u_id)
            elif sent.split()[0] == "/del":
                self.__delUser(u_id)
            else:
                self.__bot.sendMessage (chat_id = u_id, text = self.__readans("NotThere"))
        else:
            self.__bot.sendMessage(chat_id=u_id, text = "Hi, " + (msg[u'message'][u'from'][u'first_name'] if msg[u'message'][u'from'][u'first_name'] != "" else msg[u'message'][u'from'][u'username']))

    def __showVp (self, u_id): # TODO program
        """
        sends current vertretungsplan to user with telegram id u_id
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __showInfo (self, u_id): # TODO program
        """
        sends inserted courses to user with telegram id u_id
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __setURL (self, u_id): # TODO program
        """
        sets the sid of the user with telegram id u_id
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __addUser (self, u_id): # TODO program
        """
        adds the user with the telegram id u_id into our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __delUser (self, u_id): # TODO program
        """
        deletes the user with the telegram id u_id from our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __readans (self, cmd):
        """
        reads commando-answers from answers file that are static text to response 
        """
        ansfile = open("answers.txt", "r") # answers file is answers.txt
        anslines = ansfile.readlines()
        ansfile.close()
        print("will read cmd: " + cmd)
        
        anslino = len(anslines) # number of lines in answers file
        in_cmd = False
        anstext = str()

        for i in range (anslino):
            if anslines[i][0] == "#": continue # lines can be commented out with # as first letter
            if in_cmd:
                if anslines[i][0] != "-": return anstext # if line does not belong to answer anymore return text - function is finished
                else: anstext += anslines[i][1:] # line is added to text (without hyphan at beginning)
            else:
                if anslines[i][0] == "/": # if beginning of line fits beginning of command lines
                    if anslines[i][1:].strip() == cmd: in_cmd = True # following text belongs to command specific text output
        
        return anstext # EOF rescue return
                
if __name__ == "__main__":
    b = Archebot()
    while True:
        b.handle()
