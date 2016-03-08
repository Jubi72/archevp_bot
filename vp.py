import sqlite3
import urllib.request
import os
from datetime import datetime
import time
from bs4 import BeautifulSoup
import hashlib

VALID_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890./ "

class Vp():
    def __init__(self, website, sid, database):
        """
        initialize Variables and the database
        """
        self.__website = website
        self.__databaseFile = database
        createDatabase = not os.path.exists(self.__databaseFile)
        self.__database = sqlite3.connect(self.__databaseFile)
        self.__cursor = self.__database.cursor()
        self.__lastChange = "" # date and time, when the last change has happend
        self.__sid = sid
        self.__websiteHash = ""
        if (createDatabase):
            self.__createDatabase()


    def __checkInput(self, string):
        """
        check if the string only got valid characters
        """
        for char in string:
            if (not char in VALID_CHARS):
                return False
        return True


    def __createDatabase(self):
        """
        Create the tables in the database
        """
        sql_command = """
            CREATE TABLE user ( 
                userId INTEGER PRIMARY KEY, 
                username VARCHAR(32) DEFAULT 0,
                sid VARCHAR(32) DEFAULT 0,
                joining TIMESTAMP);
        """
        self.__cursor.execute(sql_command)

        sql_command = """
            CREATE TABLE entry (
                entryId INTEGER PRIMARY KEY,
                date DATE,
                day CHAR(10),
                hour INTEGER,
                course CHAR(10),
                lesson CHAR(10),
                change CHAR(64));
        """
        self.__cursor.execute(sql_command)

        sql_command = """
            CREATE TABLE course (
                userId INTEGER NOT NULL,
                course CHAR(10) NOT NULL,
                lessonStart CHAR(10) NOT NULL,
                FOREIGN KEY(userId) REFERENCES user(userId) ON UPDATE CASCADE,
                PRIMARY KEY (userId, course, lessonStart));
        """
        self.__cursor.execute(sql_command)

        self.__database.commit()

    def isAuthorised(self, userId):
        """
        Returns if the given User is Authorised
        """
        sql_command = """
            SELECT userId
            FROM user
            WHERE userId = ?
        """
        self.__cursor.execute(sql_command, (userId,))
        return (self.__cursor.fetchone() != None)


    def checkUser(self, userId, url):
        """
        checks whether a user is valid and add this user to the database 
        """
        sid = url[url.find("=")+1:]
        if (not self.__checkInput(sid)):
            print("Authentification failed: input='"+url+"'")
            return ("Anmeldung fehlgeschlagen.") #TODO: language file
        page = urllib.request.urlopen(self.__website.format(sid = sid))\
                .read().decode('cp1252')
        
        phrase = "Sie sind angemeldet als <strong>"
        index = page.find(phrase)
        if (index > 0):
            index += len(phrase)
            lenUsername = 0
            while (page[index + lenUsername] != "<"):
                lenUsername += 1

            username = page[index:index+lenUsername]

            sql_command = """
                SELECT username
                FROM user
                WHERE userId = ?
            """
            self.__cursor.execute(sql_command, (userId,))
            prevUsername = self.__cursor.fetchone()

            if (prevUsername == None):
                print("New user authentificated userId="+str(userId)\
                        +" username='"+username+"'")

                sql_command = """
                    INSERT INTO user (userId, username, sid, joining)
                    VALUES (?, ?, ?, ?) 
                """
                self.__cursor.execute(sql_command,\
                        (userId, username, sid, datetime.now()))
                
                self.__database.commit()
                return ("Anmeldung erfolgreich als " + username)#TODO

            else:
                prevUsername = prevUsername[0]
                print("User reauthentificated id="+str(userId)\
                        +" ('"+prevUsername+"'->'"+username+"')")
                if (prevUsername != username):
                    sql_command == """
                        UPDATE user
                        SET username = ?
                        WHERE userId = ?
                    """
                    self.__cursor.execute(sql_command, (username, userId))
                    self.__database.commit()

                return ("Anmeldung erfolgreich als {username}"\
                        .format(username=username))

        else:
            print("User authentification failed id=" + str(userId)+ " sid='"+sid+"'")
            return ("Anmeldung fehlgeschlagen.") #TODO: language file
                


    def addUserSubjects(self, userId, subjects):
        """
        add all given subjects to the user
        """
        if (not self.isAuthorised(userId)):
            return ("Anmeldung erforderlich")

        subjects = subjects.strip().split(",")
        for i in range(len(subjects)):
            subjects[i] = subjects[i].strip().split(" ")
            if (len(subjects[i]) == 1):
                subjects[i].append("")
            subjects[i][1] = subjects[i][1].strip() + "%"
            subjects[i] = tuple(subjects[i])

        added = 0
        failed = 0
        equal = 0

        # Check input
        testedSubjects = []
        for subject in subjects:
            if (self.__checkInput(subject[0])
                    and self.__checkInput(subject[1][:-1])):
                testedSubjects.append(subject)
            else:
                failed += 1
        subjects = testedSubjects
        
        subjects = list(set(subjects)) #Remove dublicates

        # Get current subjects
        sql_command = """
            SELECT course, lessonStart
            FROM course
            WHERE userId = ?
        """
        self.__cursor.execute(sql_command, (userId,))
        curSubjects = self.__cursor.fetchall()

        #insert subjects into the database
        sql_command = """
            INSERT INTO course (userId, course, lessonStart)
            VALUES (?, ?, ?)
        """
        addedSubjects = str()
        for elem in subjects:
            if (elem in curSubjects):
                equal += 1
            else:
                self.__cursor.execute(sql_command, (userId,)+elem)
                added += 1
                addedSubjects += elem[0]+" "+elem[1] + ", "

        self.__database.commit()
        print("Subject added userId="+str(userId)+" added="+str(added)\
                +" equal="+str(equal)+" failed="+str(failed))
        
        if (added == 0):
            return ("Keine Kurse dazugekommen.")

        elif (added == 1):
            return ("Dazugekommener Kurs: " + addedSubjects[:-2])

        else:
            return ("Dazugekommene Kurse: " + addedSubjects[:-2])


    def delUserSubjects(self, userId, subjects):
        """
        delete all given subjects from the user
        """
        subjects = subjects.split(",")
        oldSubjects = []
        for i in range(len (subjects)):
            if (not self.__checkInput(subjects[i])):
                continue
            oldSubjects.append(subjects[i].strip().split(" ", 1))
            if (len(oldSubjects[-1]) == 1):
                oldSubjects[-1].append("")
            oldSubjects[-1][1] += "%"
            oldSubjects[-1] = tuple(oldSubjects[-1])

        subjects = list(set(oldSubjects)) # Remove dublicates
        
        sql_command = """
            DELETE FROM course
            WHERE userId = ?
            AND course = ?
            AND lessonStart = ?
        """

        for subject in subjects:
            self.__cursor.execute(sql_command, (userId,) + subject)
        self.__database.commit()

        return ("Ok, alle gegebenen Kurse entfernt")
        


    def resetUserSubjects(self, userId):
        """
        deletes all subjects from the user
        """
        sql_command = """
            DELETE FROM course
            WHERE userId = ?
        """
        print("User resetted all subjects userId="+str(userId))
        self.__cursor.execute(sql_command, (userId,))
        self.__database.commit()
        return ("Reset erfolreich")


    def getUserInfo(self, userId):
        """
        returns the info of the user as a message string Info includes
        all subjects of the user and an information
        """
        sql_command = """
            SELECT course 
            FROM course
            WHERE userId = ?
        """
        subjects = ""
        self.__cursor.execute(sql_command, (userId,))
        for (subject,) in self.__cursor.fetchall():
            subjects += "\n" + subject 

        return ("Deine Kurse sind: "+ subjects)
        

    def getUserStatus(self, userId):
        """
        returns the current vp Status from the user as a message string
        """
        sql_command = """
            SELECT date, day, hour, course, lesson, change 
            FROM course
            NATRUAL JOIN entry
            WHERE userId = ?
            AND date >= ?
        """
        self.__curosr.execute(sql_command,\
                (userId, datetime.date(datetime.now())))
        print(self.__cursor.fetchall())
        for (date, day, hour, course, lesson, change)\
                in self.__curosr.fetchall():
            pass

    def getUpdates(self):
        """
        returns the changes of the vp for every user in the form
        [(userId, "message"), (userId2, "message"), ...]
        """
        page = urllib.request.urlopen(self.__website\
                .format(sid=self.__sid)).read().decode("cp1252")

        if (not page):
            print("failed to load vp")
            return ([])

        #check if the date has changed
        if (self.__websiteHash == hashlib.sha256(page.encode()).hexdigest()):
            return ([])

        self.__websiteHash = hashlib.sha256(page.encode()).hexdigest()
        
        entries = []

        soup = BeautifulSoup(page)
        dates = [date.text.split()[-2:] for date in soup.findAll("nobr")[1:]]
        tables = soup.findAll("table")
        for i in range(len(tables)):
            weekday = dates[i][0]
            date = dates[i][1].replace("(", "").replace(")", "")
            date = time.strptime(date, "%d.%m.%Y")
            date = time.strftime("%Y-%m-%d", date)
            dates[i] = date

            for row in tables[i].findAll("tr")[1:]:
                doubleEntry = row.findAll("td")
                doubleEntry = [doubleEntry[:3], doubleEntry[3:]]
                for entry in doubleEntry:
                    #Skip crossed entrys
                    if (entry[2].findAll("s")):
                        continue
                    else:
                        #get unformatted text
                        for i in range(len(entry)):
                            entry[i] = entry[i].text.strip()

                    # skip emty entries
                    if (entry[1] == '' and entry[2] == ''):
                        continue

                    # delete annoying chars
                    entry[2] = entry[2].replace("\r", "")
                    entry[2] = entry[2].replace("\n", "")
                    entry[2] = entry[2].replace("\xa0", "")
                    while ("  " in entry[2]):
                        entry[2] = entry[2].replace("  ", " ")
                    
                    #get all course/class
                    if ("+" in entry[1]):
                        # dublicate this entry to get a entry for each class
                        grade = entry[1].split("/")[0].strip()
                        class1 = entry[1].split("/")[1].split("+")[0].strip()
                        class2 = entry[1].split("/")[1].split("+")[1].strip()

                        lesson = ""
                        if (len(entry[1].split()) > 1):
                            lesson = entry[1].split()[-1]
                        
                        numbers = [str(i) for i in range(10)]
                        hours = []
                        for char in entry[0]:
                            if (char in numbers):
                                hours.append(int(char))

                        for hour in hours:
                            entries.append([date, weekday, hour,\
                                    grade+"/"+class1, lesson, entry[2]])
                            entries.append([date, weekday, hour,\
                                    grade+"/"+class2, lesson, entry[2]])

                    else:
                        info = entry[1].split() 
                        grade = ""
                        lesson = ""

                        if (len(info) == 1):
                            grade = info[0]

                        elif (len(info) == 2):
                            grade, lesson = info

                        else:
                            grade = info[0]
                            lesson = info[1]
                            for string in info[2:]:
                                lesson += " "+string

                        numbers = [str(i) for i in range(10)]
                        hours = []
                        for char in entry[0]:
                            if (char in numbers):
                                hours.append(int(char))

                        for hour in hours:
                            entries.append([date, weekday, hour,\
                                    grade, lesson, entry[2]])
                        
        for entry in entries:
            print(entry)



if (__name__ == "__main__"):
    vp = Vp("http://archenhold.de/api/vp.php?sid={sid}",\
            "q3YvFZI6qbpP0AKeNlI3PzUqmwEFv3IV",\
            "telegramBot.db")
    vp.checkUser(1,"q3YvFZI6qbpP0AKeNlI3PzUqmwEFv3IV")

    vp.addUserSubjects(1, "10 WInf, g33, g13")
    vp.delUserSubjects(1, "10 WInf, g33, g13 3")
    #vp.getUpdates()

