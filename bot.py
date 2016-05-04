#!/usr/bin/python

# from pprint import pprint # better error printing in msg-dics 
import telepot as tp
import vp

class Archebot:
    """
    runs a bot wich can read the vertretungsplan and other things
    needed files: configuration file, answer file
    """

    def __init__ (self):
        """
        initialize variables, set the token, curoff and the Bot
        """
        token = str()
        self.__curoff = 0
        
        conffile = open("avp.cfg","r") # configuration file name: avp.cfg
        conflines = conffile.readlines()
        conffile.close()
        
        for line in conflines:
            if line[0] == "#": continue # skip outcommented lines
            if line.split() == []: continue # skip empty lines
            elif line.split()[0] == "telegram_token": # telegram_token has to be first word in line
                token = line.split()[1][1:-1] # characters between the "
                break # don't check other lines -> first appearance is valid
        print(token)
        
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
                self.__setURL(msg)
            elif sent.split()[0] == "/add":
                self.__addUser(msg)
            elif sent.split()[0] == "/del":
                self.__delUser(u_id)
            else:
                self.__bot.sendMessage (chat_id = u_id, text = self.__readans("NotThere"))
        else:
            self.__bot.sendMessage(chat_id=u_id, text = "Hi, " + (msg[u'message'][u'from'][u'first_name'] if msg[u'message'][u'from'][u'first_name'] != "" else msg[u'message'][u'from'][u'username']))

    def __showVp (self, u_id): # TODO program
        """
        pre:  u_id is valid telegram user id
        post: current vertretungsplan is sent to u_id user
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __showInfo (self, u_id): # TODO program
        """
        pre:  u_id is valid telegram user id
        post: registered courses are sent to u_id user
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __setURL (self, msg): # TODO program
        """
        pre:  msg is message sent by user in valid telepot message format
        post: sid of the user is set and if did not happen before added to database
        """
        u_id = msg[u'message'][u'from'][u'id']
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __addUser (self, u_id): # TODO program
        """
        pre:  u_id is valid telegram user id
        post: u_id user is added into our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __delUser (self, u_id): # TODO program
        """
        pre:  u_id is valid telegram user id
        post: u_id user is deleted from our database (if confirmed by user)
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __readans (self, cmd):
        """
        pre:  cmd is string, optimum specified in answers file
        post: commando-answer from answer file is returned (not sent!)
        """
        ansfile = open("answers.txt", "r") # answers file is answers.txt
        anslines = ansfile.readlines()
        ansfile.close()
        
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

        if anstext == "": anstext = self.__readans ("notThere") # rescue: not empty string but message for not available command sent
        
        return anstext # EOF rescue return
                
if __name__ == "__main__":
    b = Archebot()
    while True:
        b.handle()
