import sqlite3
import urllib.request
import os
from datetime import datetime
import time
from bs4 import BeautifulSoup
import hashlib
import calendar

VALID_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890./ "

CHANGE_ADDED = 0
CHANGE_UPDATED = 1
CHANGE_REMOVED = 2

CHANGE_MESSAGES = ["ADD", "UPD", "DEL"]

class Vp():
    def __init__(self, website, websiteVpDate, sid, database):
        """
        initialize Variables and the database
        """
        self.__website = website
        self.__websiteVpDate = websiteVpDate
        self.__databaseFile = database
        createDatabase = not os.path.exists(self.__databaseFile)
        self.__database = sqlite3.connect(self.__databaseFile)
        self.__cursor = self.__database.cursor()
        self.__lastChange = "" # date and time, when the last change has happend
        self.__sid = sid
        self.__websiteHash = ""
        self.__firstUpdate = False
        if (createDatabase):
            self.__firstUpdate = False
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
                date DATE,
                hour INTEGER,
                course CHAR(10),
                lesson CHAR(10),
                change CHAR(64),
                changed CHAR(1) DEFAULT 1,
                lastchange INTEGER DEFAULT {added},
                PRIMARY KEY (date, hour, course, lesson));
        """.format(added = CHANGE_ADDED)
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
                    and self.__checkInput(subject[1][:-1])
                    and subject[0].strip() != ""
                    and len(subject[0])<=10
                    and len(subject[1])<=10):
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

        removed = 0
        failed = 0
        for i in range(len (subjects)):
            if (not self.__checkInput(subjects[i])):
                failed += 1
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
                AND lessonStart LIKE lesson
                AND date >= ?
        """
        self.__curosr.execute(sql_command,\
                (userId, datetime.date(datetime.now())))
        for (date, day, hour, course, lesson, change)\
                in self.__curosr.fetchall():
            pass


    def __getWebsiteDates(self, page):
        """
        Returns all Dates found on the website
        """
        soup = BeautifulSoup(page)
        dates = [date.text.split()[-2:] for date in soup.findAll("nobr")[1:]]
        for i in range(len(dates)):
            date = dates[i][1].replace("(", "").replace(")", "")
            date = time.strptime(date, "%d.%m.%Y")
            date = time.strftime("%Y-%m-%d", date)
            dates[i] = date
        return dates


    def __getWebsiteEntries(self, page, dates):
        """
        Returns all Entries found on the given page (HTML-Code)
        The returned list has the format:
        [[(date, hour, course, lesson), change], ...]
        """
        entries = []

        soup = BeautifulSoup(page)
        tables = soup.findAll("table")
        for table in range(len(tables)):
            for row in tables[table].findAll("tr")[1:]:
                doubleEntry = row.findAll("td")
                doubleEntry = [doubleEntry[:3], doubleEntry[3:]]
                for entry in doubleEntry:
                    #Skip crossed entrys
                    if (entry[2].findAll("s")):
                        continue
                    else:
                        #get unformatted text
                        for col in range(len(entry)):
                            entry[col] = entry[col].text.strip()

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
                            entries.append([(dates[table], hour,\
                                    grade+"/"+class1, lesson), entry[2]])
                            entries.append([(dates[table], hour,\
                                    grade+"/"+class2, lesson), entry[2]])

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
                            entries.append([(dates[table], hour,\
                                    grade, lesson), entry[2]])
        return (entries)


    def __getDatabaseEntries(self, dates):
        """
        This function returns all database Entries from the given dates,
        which are not previosly removed
        The returned list has the format:
        [[(date, hour, course, lesson), change], ...]
        """
        databaseEntries = []
        for date in dates:
            sql_command = """
                SELECT date, hour, course, lesson, change
                FROM entry WHERE date = ?
                    AND lastchange != ?
            """
            self.__cursor.execute(sql_command, (date, CHANGE_REMOVED))
            databaseRawEntries = self.__cursor.fetchall()
            for entry in databaseRawEntries:
                databaseEntries.append([entry[:-1], entry[-1]])
        return databaseEntries


    def __databaseResetNew(self):
        """
        This function resets all entries marked to be new to be not new
        """
        sql_command = """
            UPDATE entry
            SET changed = 0
            WHERE changed = 1
        """
        self.__cursor.execute(sql_command)


    def __databaseAddEntry(self, entry):
        """
        This function gets a entry in the format:
        [("yyyy-mm-dd", hour (int), course (string), lesson (string)), change (string)]
        and trys to insert it into the database and returns if it worked
        """
        # Insert entry into the database
        sql_command = """
            INSERT INTO entry
            (date, hour, course, lesson, change)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.__cursor.execute(sql_command, entry[0]+(entry[1],))
            return True
        except:
            return False
        

    def __databaseUpdateEntry(self, entry):
        """
        This function gets a entry in the format:
        [("yyyy-mm-dd", hour (int), course (string), lesson (string)), change (string)]
        and and trys to update the entry returns if it worked
        """
        sql_command = """
            SELECT *
            FROM entry
            WHERE date = ?
                AND hour = ?
                AND course = ?
                AND lesson = ?
        """
        self.__cursor.execute(sql_command, entry[0])
        if (self.__cursor.fetchone()):
            # only the change has changed
            sql_command = """
                UPDATE entry
                SET change = ?,
                    changed = ?,
                    lastchange = ?
                WHERE date = ?
                    AND hour = ?
                    AND course = ?
                    AND lesson = ?
            """
            self.__cursor.execute(sql_command,\
                    (entry[1], True, CHANGE_UPDATED)+entry[0] )
            return True
        else:
            return False


    def __databaseRemoveEntry(self, entry):
        """
        This function gets a entry in the format:
        ("yyyy-mm-dd", hour (int), course (string), lesson (string))
        and returns if it worked
        """
        sql_command = """
            UPDATE entry
            SET changed = ?,
                lastchange = ?
            WHERE date = ?
                AND hour = ?
                AND course = ?
                AND lesson = ?
        """
        self.__cursor.execute(sql_command,\
                (True, CHANGE_REMOVED)+entry)


    def __updateDatabase(self, newEntries, oldEntries):
        """
        This function gets two list of entries from the same dates
        and insert all new Entries into the database, mark deleted
        as removed and update updated entries
        Input lists:
        [[("yyyy-mm-dd", hour (int), course (string), lesson (string)), change (string)], ...]
        """
        self.__databaseResetNew()

        addedEntries = 0
        updatedEntries = 0
        removedEntries = 0
        skippedEntries = 0
        failedEntries = 0
        
        for entry in newEntries:
            if (entry in oldEntries):
                # Already in database
                oldEntries.remove(entry)
                skippedEntries += 1

            elif (self.__databaseUpdateEntry(entry)):
                # Already in database, but different change
                updatedEntries += 1
                for elem in oldEntries[:]:
                    if (elem[0] == entry[0]):
                        oldEntries.remove(elem)

            else:
                if (self.__databaseAddEntry(entry)):
                    addedEntries += 1
                else:
                    failedEntries += 1

        for entry in oldEntries:
            # Set status to deleted
            self.__databaseRemoveEntry(entry[0])
            removedEntries+=1
            

        self.__database.commit()

        print("Update vp: Entries added="+str(addedEntries)\
                +" updated="+str(updatedEntries)\
                +" removed="+str(removedEntries)\
                +" skipped="+str(skippedEntries)\
                +" failed="+str(failedEntries))


    def __getUpdateMessages(self):
        """
        This function read all database entries and return messages
        for all users, who had changes
        List format:
        [(userId (int), message (string)), ...]
        """
        sql_command = """
            SELECT userId, date, hour, entry.course, lesson, lastchange, change
            FROM course
                JOIN entry ON course.course COLLATE NOCASE = entry.course
                    AND lesson LIKE lessonStart
            WHERE changed = 1
            ORDER BY userId, date, hour
        """
        self.__cursor.execute(sql_command)
        changes = self.__cursor.fetchall()

        curUser = -1
        curDate = ""
        curMessage = ""
        messages = []
        print("changes:",changes)
        for change in changes:
            if (changes[0] != curUser):
                if (curUser != -1):
                    messages.append((curUser, curMessage))
                curUser = changes[0]
                curDate = ""
                curMessage = "Aenderung am Vertretungsplan:"
            if (curDate != change[1]):
                curDate = change[1]
                curMessage += "\n\n" + "{weekday} der {day}:"\
                        .format(weekday = calendar.day_name[datetime.strptime(curDate, "%Y-%m-%d").weekday()],\
                            day = datetime.strptime(curDate, "%Y-%m-%d").strftime("%d.%m.%Y"))
            
            curMessage += "\n" + "  {std}. Std: {lastchange} {course} {lesson} - {change}"\
                    .format(std = change[2],\
                        course = change[3],\
                        lesson = change[4],\
                        lastchange = CHANGE_MESSAGES[change[5]],\
                        change = change[6])
        if (curUser != -1):
            messages.append((curUser, curMessage))
        return messages
        

    def getUpdates(self):
        """
        This function checks if the vp website has changed
        and returns the changes of the vp for every user in the form
        [(userId, "message"), (userId2, "message"), ...]
        """
        try:
            page = urllib.request.urlopen(self.__website\
                .format(sid=self.__sid)).read().decode("cp1252")
            #page = open("vp.html", "rb").read().decode("cp1252")
            vpDate = urllib.request.urlopen(self.__websiteVpDate).read()
        except:
            print("Update vp: Error while loading vp website")
            return ([])

        if (not page):
            print("Update vp: sid isn't correct")
            return ([])

        #check if the date has changed
        if (self.__websiteHash == hashlib.sha256(vpDate).hexdigest()):
            # Website hasn't changed
            return ([])

        self.__websiteHash = hashlib.sha256(vpDate).hexdigest()

        # get all website enrtries
        websiteDates = self.__getWebsiteDates(page)
        websiteEntries = self.__getWebsiteEntries(page, websiteDates)

        # get all database entries
        databaseEntries = self.__getDatabaseEntries(websiteDates)
        
        # update the database by comparing website and database entries
        self.__updateDatabase(websiteEntries, databaseEntries)

        # Get messages for users, who has changed entries form the vp
        if (self.__firstUpdate):
            self.__firstUpdate = False
            # first update -> all entries new -> do not send all to users
            return ([])
        return (self.__getUpdateMessages())


