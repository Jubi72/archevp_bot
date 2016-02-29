from pprint import pprint # bessere Druckfunktion für Errors
import telepot as tp

class archebot:

    def __init__ (self):
        self.token = str()
        self.bot = tp.Bot(None)
        self.curoff = 0

    def start(self):
        self.token = "217111679:AAHL20Jw5JI5k7v1ByQ3B25UdQrg-DoQFtg" #sollte irgendwie noch verschlüsselt werden
        self.bot = tp.Bot(self.token)
        self.setcuroff()

    def setcuroff(self):
        allup = self.bot.getUpdates()
        self.curoff = allup[-1][u'update_id'] + 1

    def handle(self): # example handle
        response = self.bot.getUpdates(offset=self.curoff)
        if response != []:
            for one in response:
                self.bot.sendMessage(chat_id=one[u'message'][u'from'][u'id'],
                                     text = "You said " + one[u'message'][u'text'])
            self.setcuroff()

if __name__ == "__main__":
    b = archebot()
    b.start()
    while True:
        b.handle()
