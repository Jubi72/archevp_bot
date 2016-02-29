# from pprint import pprint # better error printing in msg-dics 
import telepot as tp

class archebot:

    def __init__ (self):
        self.token = str()
        self.bot = tp.Bot(None)
        self.curoff = 0

    def start(self):
        self.token = "217111679:AAHL20Jw5JI5k7v1ByQ3B25UdQrg-DoQFtg" #TODO: should still get encrypted anyway
        self.bot = tp.Bot(self.token)
        self.setcuroff()

    def setcuroff(self):
        allup = self.bot.getUpdates()
        if allup == []:
            self.curoff = 0
        else:
            self.curoff = allup[-1][u'update_id'] + 1

    def handle(self):
        response = self.bot.getUpdates(offset=self.curoff)
        if response != []:
            for message in response: self.response(message)
            self.setcuroff()

    def response (self, msg):
        sent = msg[u'message'][u'text'] # sent message
        u_id = msg[u'message'][u'from'][u'id'] # user-id = chat-id
        if sent[0] == "/":
            if sent.split()[0] == "/help":
                self.bot.sendMessage(chat_id = u_id,
                                     text = """Dies ist der inoffizielle Archenhold-Vertretungsplan-Bot.

*Mit /vp kannst du deinen aktuellen Vertretungsplan anzeigen, sofern du den Bot konfiguriert hast.
*Mit /info zeigst du deine aktuellen Kurse bzw. Klassen an. Du solltest auch z. B. Q1 eintragen, wenn du dich im ersten Semester befindest.
*Mit /url fügst du deinen Login-URL hinzu. Diesen findest du unter http://pi.archenhold.de/service/vertretungsplan unter "Zugangscode auf andere Geräte übertragen". Kopiere einfach diesen Link und füge ihn ein.
*Mit /add fügst du einen deiner Kurse hinzu.
*Mit /del löschst du einen deiner Kurse.
    *Diese werden dir als Tastatur zum Anklicken angezeigt.
Mit /help zeigst du diese Hilfe an.""")
            elif sent.split()[0] in ["/vp", "/info", "/url", "/add", "/del"]:
                self.bot.sendMessage (chat_id = u_id, text = "Das Kommando wird bald ergänzt.") #TODO: Richtige Namen einfügen
            else:
                self.bot.sendMessage (chat_id = u_id, text = "Sorry, aber das Kommando ist leider nicht verfügbar. Schau dir doch mit /help eine Liste verfügbarer Kommandos an.")
        else:
            self.bot.sendMessage(chat_id=u_id, text = "Hi, " + (msg[u'message'][u'from'][u'first_name'] if msg[u'message'][u'from'][u'first_name'] != "" else msg[u'message'][u'from'][u'username']))
        

if __name__ == "__main__":
    b = archebot()
    b.start()
    while True:
        b.handle()
