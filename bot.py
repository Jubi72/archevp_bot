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
        self.curoff = allup[-1][u'update_id']

    def handle(self, msg):
        response = self.bot.getUpdates(offset=curoff)
