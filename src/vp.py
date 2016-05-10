import sqlite3
import urllib.request
import os
from datetime import datetime
import time
from bs4 import BeautifulSoup
import hashlib
import calendar
import configparser
import logging

VALID_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890./ "

CHANGE_ADDED = 0
CHANGE_UPDATED = 1
CHANGE_REMOVED = 2

CHANGE_MESSAGES = ["ADDED", "UPDATED", "REMOVED"]

class Vp():
    def __init__(self, website, websiteVpDate, sid, database, language, logger):
        """
        initialize Variables and the database
        """
        self.__website = website
        self.__websiteVpDate = websiteVpDate
        self.__databaseFile = "data/" + database
        createDatabase = not os.path.exists(self.__databaseFile)
        self.__database = sqlite3.connect(self.__databaseFile)
        self.__cursor = self.__database.cursor()
        self.__lastChange = "" # date and time, when the last change has happend
        self.__sid = sid
        self.__websiteHash = ""
        self.__firstUpdate = False
        self.__translation = configparser.ConfigParser()
        language = "data/language/" + language + ".txt"
        self.__translation.read(language)
        if (createDatabase):
            self.__firstUpdate = True
            self.__createDatabase()
        self.__logger = logger


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


    def getUserHelp(self, userId):
        """
        Send the user different help depending if they are registered
        """
        if (self.isAuthorised(userId)):
            self.__logger.debug("[vp] USER help requested - registered id={userId}"\
                        .format(userId=userId))
            return self.__translation['user']['HELP_REGISTERED']
        else:
            self.__logger.debug("[vp] USER help requested - newbie id={userId}"\
                        .format(userId=userId))
            return self.__translation['user']['HELP_NEWBIE']


    def checkUser(self, userId, url):
        """
        checks whether a user is valid and add this user to the database 
        """
        # Check if the input is correct
        sidBegin = url.find("=")+1
        if (sidBegin == len(url)):
            self.__logger.debug ("[vp] USER Authentification failed: input='{url}'"\
                    .format(url=url))
            return (self.__translation['user']["AUTH_FAILED"])
            
        sid = url[sidBegin:]
        # Check if the input has only valid chars
        if (not self.__checkInput(sid)):
            self.__logger.debug ("[vp] USER Authentification failed: input='{url}'"\
                    .format(url=url))
            return (self.__translation['user']["AUTH_FAILED"])

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
                self.__logger.info("[vp] USER authentificated userId={userId} username={username}"
                        .format(userId = userId, username = username))

                sql_command = """
                    INSERT INTO user (userId, username, sid, joining)
                    VALUES (?, ?, ?, ?) 
                """
                self.__cursor.execute(sql_command,\
                        (userId, username, sid, datetime.now()))

                # insert public course to user
                sql_command = """
                    INSERT INTO course (userId, course, lessonStart)
                    VALUES (?, "", "%")
                """
                self.__cursor.execute(sql_command, (userId,))
                
                self.__database.commit()
                return (self.__translation["user"]["AUTH_SUCCESSFUL"])

            else:
                prevUsername = prevUsername[0]
                self.__logger.debug("[vp] USER reauthentificated id={userId} ({name}->{newname})"\
                        .format(userId = userId, name = prevUsername, newname = username))
                if (prevUsername != username):
                    sql_command == """
                        UPDATE user
                        SET username = ?
                        WHERE userId = ?
                    """
                    self.__cursor.execute(sql_command, (username, userId))
                    self.__database.commit()

                return (self.__translation["user"]["AUTH_SUCCESSFUL"])

        else:
            self.__logger.debug("[vp] USER authentification failed id={userId} sid={sid}"\
                    .format(userId=userId, sid=sid))
            return (self.__translation["user"]["AUTH_FAILED"])


    def delUser(self, userId, userInput):
        """
        Delete the user from the databse
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])

        if (str(userId) != userInput.strip()):
            return (self.__translation["user"]["USER_DELETE_UID"]
                    .format(userId = userId).replace("\n", " "))

        # Delete user courses
        sql_command = """
            DELETE FROM course
            WHERE userId = ?
        """
        self.__cursor.execute(sql_command, (userId,))

        # Delete user from database
        sql_command = """
            DELETE FROM user
            WherE userId = ?
        """
        self.__cursor.execute(sql_command, (userId,))
        self.__database.commit()

        return (self.__translation["user"]["USER_DELETED"])


    def addUserSubjects(self, userId, subjects):
        """
        add all given subjects to the user
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])

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
        self.__logger.debug("[vp] USER subjects add userId="+str(userId)+" added="+str(added)\
                +" equal="+str(equal)+" failed="+str(failed))
        
        if (added == 0):
            return (self.__translation["courses"]["ADDED_NOTHING"])

        elif (added == 1):
            return (self.__translation["courses"]["ADDED_SINGLE"]\
                    .format(course=addedSubjects[:-2]))

        else:
            return (self.__translation["courses"]["ADDED_MULTIPLE"]\
                    .format(courses = addedSubjects[:-2]))


    def delUserSubjects(self, userId, subjects):
        """
        delete all given subjects from the user
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])

        subjects = subjects.split(",")
        oldSubjects = []

        removed = 0
        failed = 0
        for i in range(len(subjects)):
            if (not self.__checkInput(subjects[i])
                    or subjects[i].strip() == ""):
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
            removed += 1
        self.__database.commit()

        self.__logger.debug("[vp] USER subjects rem userId={userId} removed={removed} failed={failed}"
            .format(userId = userId,
                removed = removed,
                failed = failed))
        return (self.__translation["courses"]["REMOVED_SOME"])
        

    def resetUserSubjects(self, userId):
        """
        deletes all subjects from the user
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])

        sql_command = """
            DELETE FROM course
            WHERE userId = ?
                AND course != ""
        """
        self.__logger.debug("[vp] USER subjects del userId="+str(userId))
        self.__cursor.execute(sql_command, (userId,))
        self.__database.commit()
        return (self.__translation["courses"]["REMOVED_ALL"])


    def getUserInfo(self, userId):
        """
        returns the info of the user as a message string Info includes
        all subjects of the user and an information
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])


        sql_command = """
            SELECT course, lessonStart
            FROM course
            WHERE userId = ?
            AND course != ""
        """
        subjects = ""
        self.__cursor.execute(sql_command, (userId,))
        for (subject, lesson) in self.__cursor.fetchall():
            subjects += "\n * " + subject + " " + lesson[:-1]

        return (self.__translation["courses"]["CURRENT"]
                    .format(courses = subjects))
        

    def getUserStatus(self, userId):
        """
        returns the current vp Status from the user as a message string
        """
        if (not self.isAuthorised(userId)):
            return (self.__translation["user"]["AUTH_REQUIRED"])
 
        sql_command = """
            SELECT date, hour, entry.course, lesson, change
            FROM course
                JOIN entry ON course.course COLLATE NOCASE = entry.course
                    AND lesson LIKE lessonStart
            WHERE userId = ?
                AND date >= ?
                AND lastchange != ?
            ORDER BY date, hour
        """
        self.__cursor.execute(sql_command,\
                (userId, datetime.date(datetime.now()), CHANGE_REMOVED))
        
        allChanges = self.__cursor.fetchall()

        if (allChanges == []):
            return (self.__translation["vp"]["NO_CHANGES"])

        curDate = ""
        message = self.__translation["vp"]["HEADER"]
        for change in allChanges:
            if (curDate != change[0]):
                curDate = change[0]
                message += "\n " + self.__translation["vp"]["DAY"]\
                      .format(weekday = self.__translation['weekday'][calendar.\
                         day_name[datetime.strptime(curDate, "%Y-%m-%d").weekday()]\
                            .upper()],\
                         date = datetime.strptime(curDate, "%Y-%m-%d")\
                            .strftime(self.__translation['vp']["DATE"]))

            course = change[2]
            if (course):
                course += " " + change[3]
                message += "\n  " + self.__translation["vp"]["CHANGE"]\
                    .format(hour = change[1],\
                        course = course,\
                        change = change[4])

            else:
                message += "\n  * " + self.__translation["vp"]["CHANGE_WOC"]\
                    .format(hour = change[1],\
                        change = change[4])

        return message


    def __getWebsiteDates(self, page):
        """
        Returns all Dates found on the website
        """
        soup = BeautifulSoup(page, "html.parser")
        for table in soup.findAll("table"):
            table.clear()
        rawDates = soup.findAll("p")[1:]
        
        dates = []
        for rawDate in rawDates:
            # Skip emty entries
            if (rawDate.text.strip() == ""):
                continue

            strDate = rawDate.text.split()[-1]
            strDate = strDate.replace("(", "").replace(")", "")
            date = time.strptime(strDate, "%d.%m.%Y")
            date = time.strftime("%Y-%m-%d", date)
            dates.append(date)
        return dates

    
    def __getWebsiteEntriesCourses(self, cell):
        """
        this function gets a cell (string) with the course
        examples: "7/1 Ma", "8/3+4 FrT", "G30/130 Ge"
        and returns all curses and the lesson
        (("curse1", "curse2", ...), "lesson")
        """
        if ("+" in cell):
            classes = cell.split(" ")[0].split("/")[1].split("+")

            lesson = ""
            if (len(cell.split(" ", 1)) > 1):
                lesson = cell.split(" ", 1)[1]

            for i in range(len(classes)):
                classes[i] = cell.split("/")[0].strip() + "/" + classes[i].strip()
            return (tuple(classes), lesson)

        elif (len(cell)>0 and cell[0].lower() in "lg" and "/" in cell):
            courses = cell[1:].split(" ")[0].split("/")
            lesson = ""

            if (len(cell.split(" ", 1)) > 1):
                lesson = cell.split(" ", 1)[1]

            for i in range(len(courses)):
                courses[i] = cell[0]+courses[i].strip()
            return (tuple(courses), lesson)

        info = cell.split(" ", 1) 
        grade = info[0]
        lesson = ""
        if (len(info) > 1):
            lesson = info[1]
        return ((grade,), lesson)


    def __getWebsiteEntryHours(self, cell):
        """
        This function gets a cell (string) with the hours
        with the format: "1.", "0.-2.", "0./3.-5."
        and returns all as a tupel with this format:
        (hour1 (int), hour2 (int), ...)
        """
        cell = cell.replace(".", "")
        cell = cell.replace(" ", "")
        cell = cell.replace("\t", "")
        cell = cell.replace("\r", "")
        cell = cell.replace("\n", "")
        cell = cell.replace("\xa0", "")

        if (len(cell)==1):
            return (int (cell),)

        hours = []
        hoursList = cell.split("/")

        for i in range(len(hoursList)):
            if ("-" in hoursList[i]):
                hourRange = hoursList[i].split("-")
                hours += [j for j in range(int(hourRange[0]), int(hourRange[1])+1)]
            else:
                hours += [int(hoursList[i])]

        return tuple(hours)


    def __getWebsiteEntriesRow(self, date, row):
        """
        This function get a one row and 3 col html-table and returns
        a table in this format:
        [[(date, hour, course, lesson), change], ...]
        """
        #Skip crossed entrys
        if (row[2].findAll("s")):
            return ([])
        else:
            #get unformatted text
            for col in range(len(row)):
                row[col] = row[col].text.strip()

        # delete annoying chars
        for i in range(len(row)):
            row[i] = row[i].replace("\t", " ")
            row[i] = row[i].replace("\r", " ")
            row[i] = row[i].replace("\n", "")
            row[i] = row[i].replace("\xa0", " ")
            while ("  " in row[i]):
                row[i] = row[i].replace("  ", " ")

        # skip emty entries
        if (row[1] == '' and row[2] == ''):
            return ([])

        #get all course/class, hours
        courses, lesson = self.__getWebsiteEntriesCourses(row[1])
        hours = self.__getWebsiteEntryHours(row[0])

        newEntries = []
        for hour in hours:
            for cours in courses:
                newEntries.append([(date, hour, cours, lesson), row[2]])
        return newEntries


    def __getWebsiteEntries(self, page, dates):
        """
        Returns all Entries found on the given page (HTML-Code)
        The returned list has the format:
        [[(date, hour, course, lesson), change], ...]
        """
        entries = []

        soup = BeautifulSoup(page, "html.parser")
        tables = soup.findAll("table")
        for tableIdx in range(len(tables)):
            for row in tables[tableIdx].findAll("tr")[1:]:
                doubleEntry = row.findAll("td")
                doubleEntry = [doubleEntry[:3], doubleEntry[3:]]
                for entry in doubleEntry:
                    for newEntry in self.__getWebsiteEntriesRow(dates[tableIdx], entry):
                        # check if a class has 2 entries at the same time
                        doublicate = False
                        for oldEntry in entries:
                            if (newEntry[0] == oldEntry[0]):
                                doublicate = True
                                oldEntry[1] += " " + newEntry[1]
                        if (not doublicate):
                            entries.append(newEntry)

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
            self.__logger.info("[vp] UPDATE: Added entry {date} {hour}. {course} {lesson}: {change}"
                    .format(date = entry[0][0],
                        hour = entry[0][1],
                        course = entry[0][2],
                        lesson = entry[0][3],
                        change = entry[1].decode()))
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
                    (entry[1], True, CHANGE_UPDATED)+entry[0])
            self.__logger.info("[vp] UPDATE: Updated entry {date} {hour}. {course} {lesson} -> {change}"
                    .format(date = entry[0][0],
                        hour = entry[0][1],
                        course = entry[0][2],
                        lesson = entry[0][3],
                        change = entry[1]))
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
        self.__logger.info("[vp] UPDATE: Removed entry {date} {hour}. {course} {lesson}"
                .format(date = entry[0],
                        hour = entry[1],
                        course = entry[2],
                        lesson = entry[3]))
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

        self.__logger.info("[vp] UPDATE: Entries added="+str(addedEntries)\
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
        for change in changes:
            if (change[0] != curUser):
                if (curUser != -1):
                    messages.append((curUser, curMessage))
                curUser = change[0]
                curDate = ""
                curMessage = self.__translation["vp"]["CHANGE_HEADER"]
            if (curDate != change[1]):
                curDate = change[1]
                curMessage += "\n " + self.__translation["vp"]["DAY"]\
                    .format(weekday = self.__translation["weekday"]
                                [calendar.day_name[datetime.strptime(curDate, "%Y-%m-%d").weekday()].upper()],\
                            date = datetime.strptime(curDate, "%Y-%m-%d").strftime(self.__translation["vp"]["DATE"]))
            
            course = change[3]
            if (course):
                course += " " + change[4]
                curMessage += "\n  " + self.__translation["vp"]["CHANGE_NEW"]\
                    .format(hour = change[2],\
                        course = course,\
                        lastchange = self.__translation["change"][CHANGE_MESSAGES[change[5]].upper()],\
                        change = change[6])

            else:
                curMessage += "\n  " + self.__translation["vp"]["CHANGE_WOC"]\
                    .format(std = change[2],\
                        lastchange = CHANGE_MESSAGES[change[5]].upper(),\
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
            vpDate = urllib.request.urlopen(self.__websiteVpDate).read()
        except:
            print("[vp] UPDATE: Error while loading vp website")
            return ([])

        if (not page):
            print("[vp] UPDATE: sid isn't correct")
            return ([])

        # check if the date has changed
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

