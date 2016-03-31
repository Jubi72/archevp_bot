import os

class Translation:
    def __init__(self, directory, defaultLanguage):
        self.__path = directory
        self.__defaultLanguage = defaultLanguage
        
        # The language dict has the Format:
        # {language1:{"WORD1":"translation1", ...}, ...}
        self.__languageDict = dict()

        self.__readLanguageFiles()

    def __readLanguageFiles(self):
        """
        This function read from the directory all language files
        with the ending ".lang" and add all given strings to the 
        dictionary
        """
        for filename in os.listdir(self.__path):
            if (not len(filename)>5 and filename[-5:] == ".lang"):
                # Skip not language files
                continue

            language = filename[:-5]
            self.__languageDict[language] = dict()
            lines = open(self.__path + filename).readlines()
            for line in lines:
                line = line.split("#", 1)[0].strip() #remove comments
                if (not line):
                    #skip emty lines
                    continue
                key, phrase = line.split(":", 1)
                key = key.strip()
                phrase = phrase[phrase.find("\"")+1:phrase.rfind("\"")]
                self.__languageDict[language][key] = phrase

    def get(self, key, lang = ""):
        """
        This function returns the string from the lanugage
        """
        if (lang != "" and key in self.__languageDict[lang].keys()):
            return self.__languageDict[lang][key]
        else:
            return self.__languageDict[self.__defaultLanguage][key]

