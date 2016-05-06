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
        self.__conflines = conffile.readlines()
        conffile.close()

        self.__token = self.__confread("telegram_token")
        print(token)
        self.__bot = tp.Bot(self.__token)

        self.__initvp()
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
    
    def __initvp (self):
        """
        inits the vp 
        """
        website = self.__confread("vp_addr")
        sid = self.__confread("vp_sid")
        db = self.__confread("vp_database")
        datesite = self.__confread("vpdate_addr")
        if "" in [website, sid, db, datesite]:
            print("Error: One of the vp conf values is empty")

        self.__vp = vp.Vp(website, datesite, sid, db)
            
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

    def __confread (self, var):
        """
        reads the variable got in config file
        """
        for line in self.__conflines:
            if line[0] == "#": continue # skip outcommented lines
            if line.split() == []: continue # skip empty lines
            elif line.split()[0] == var: # var has to be first word in line
                return line.split()[1] # do not read other lines, only first appearance is valid; no whitespace in value allowed

    def __response (self, msg):
        sent = msg[u'message'][u'text'] # message the bot received
        u_id = msg[u'message'][u'from'][u'id'] # user-id = chat-id
        print(u_id, msg[u'message'][u'from'][u'username'])
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
                self.__addSubj(msg)
            elif sent.split()[0] == "/del":
                self.__delSubj(msg)
            elif sent.split()[0] == "/delme":
                self.__delUser(u_id)
            elif sent.split()[0] == "/delMeREALLYiAmSUREandCAREFUL":
                self.__delUserReally(u_id)
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

    def __showInfo (self, u_id):
        """
        pre:  u_id is valid telegram user id
        post: registered courses are sent to u_id user
              if user not registered error msg is sent
        """
        if self.__vp.isAuthorised(u_id):
            self.__bot.sendMessage(chatid = u_id, text = self.__vp.getUserInfo(u_id))
        else:
            self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notReg"))

    def __setURL (self, msg):
        """
        pre:  msg is message sent by user in valid telepot message format
        post: sid of the user is set and if did not happen before added to database
        """
        u_id = msg[u'message'][u'from'][u'id']
        url = msg[u'message'][u'text'].split()[1]
        resp = self.__vp.checkUser(u_id, text).replace("E", "e")
        self.__bot.sendMessage(chat_id = u_id, text = resp)

    def __addSubj (self, msg): # TODO program
        """
        pre:  msg is message sent by user in valid telepot message format
        post: subjects are added to our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __delSubj (self, msg): # TODO program
        """
        pre:  msg is message sent by user in valid telepot message format
        post: comma separated subjects are deleted from our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __resetSubj (self, u_id): # TODO program
        """
        pre:  u_id is valid telegram user id
        post: all subjects are deleted from our database
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))

    def __delUser (self, u_id):
        """
        pre:  u_id is valid telegram user id
        post: confirmation is asked by user, command for real deletion is sent
        """
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("delUser"))

    def __delUserReally (self, u_id): # TODO program (vp.py)
        """
        pre:  u_id is valid telegram user id
        post: u_id user is deleted from our database
        """
        # TODO has to be programmed in vp.py
        self.__bot.sendMessage(chat_id = u_id, text = self.__readans("notThere"))
        #self.__bot.sendMessage(chat_id = u_id, text = self.__readans("userDeleted"))

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
