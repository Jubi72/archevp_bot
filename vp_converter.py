

Webseite = "http://archenhold.de/api/vp.php?sid=DIr3CYBQdSaS0eleqWGdj1o7htvDvpq9"

import urllib.request
 
t = urllib.request.urlopen(Webseite)

text = t.read().decode("cp1252")
"""f=open("vp.txt","r")
text = f.read()
f.close()"""
#text = ""
## Dekodierung:
"""for elem in text2:
    text+=chr(elem)"""
text = text[text.index("</p>")+4:] # ersten Absatz entfernen


gesamt_liste = []
def make1string(liste):
    # Hilfsfunktion, die in den Tabellenzellen befindlichen Informationen von der
    # Listenstruktur in die String-Struktur zu übertragen
    s = ""
    for elem in liste:
        s += elem
        s += " "
    return s[:-1]
for tag in text.split("</table>")[:-1]:
    #################### Informationen zum Datum suchen ######################
    datum = ""
    start = 0
    ende = 0
    for zeichen in tag:
        if(zeichen == "<"):
            start +=1
            if(datum != ""): break
        elif(zeichen == ">"):
            ende += 1
        elif(start == ende):
            if(zeichen.strip() != ""):
                datum += zeichen
    #print(datum)
    t,m,j,n = "","","",0
    for elem in datum.split("(")[1]:
        if(elem == "."): n+=1
        elif(elem == ")"): break
        else:
            if(n==0): t+=elem
            elif(n==1): m+=elem
            elif(n==2): j+=elem
    str_tag = ""
    wochentage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag"]
    for wt in wochentage:
        if (wt.lower() in datum.lower()):
            str_tag = wt
            break
    datum = j+"-"+m+"-"+t    
    ##########################################################################
    
    bloecke = tag.split("<td")[1:]
    akt_liste = [] # Inhalt der Tabellenzelle
    datensatz = [] # Inhalt 3 zusammengehöriger Tabellenzellen
    akt_text = ""
    durchgestrichen = False
    for block in bloecke:
        start = 1
        ende = 0
        for zeichen in block:
            if(zeichen == "<"):
                if(start == ende and akt_text.strip() != ""):
                    akt_liste.append(akt_text.strip())
                akt_text = ""
                start += 1
            elif(zeichen == ">"):
                ende += 1
            elif(start == ende):
                akt_text += zeichen
        akt = make1string(akt_liste)
        datensatz.append(akt)
        if("<s>" in block):
            durchgestrichen = True
            #print("durchgestrichen",durchgestrichen)
        if(len(datensatz) == 3):
            if(not "" in datensatz):
                st = []
                for elem in datensatz[0]:
                    if(elem in ("0","1","2","3","4","5","6","7","8","9")):
                        st.append(int(elem))
                #print(st)
                if(st != []):
                    # damit die Kopfzeile: "St." verworfen wird
                    if(durchgestrichen):
                        durchgestrichen = False
                        #print("durchgestrichen",[datum,str_tag]+datensatz)
                    else:
                        for el in st:
                            datensatz[2] = datensatz[2].replace("\r","")
                            datensatz[2] = datensatz[2].replace("\n","")
                            while("  " in datensatz[2]):
                                datensatz[2] = datensatz[2].replace("  "," ")
                            if("+" in datensatz[1]):
                                jahr = (datensatz[1].split("/")[0].strip())
                                k1 = (datensatz[1].split("/")[1].split("+")[0].strip())
                                k2 = (datensatz[1].split("/")[1].split()[0].split("+")[1].strip())
                                if(len(datensatz[1].split()) > 1): fach = datensatz[1].split()[-1]
                                #print(datensatz[1],"zwei:",jahr,k1,k2,fach)
                                gesamt_liste.append([datum,str_tag]+[el]+[jahr+"/"+k1,fach]+[datensatz[2]])
                                gesamt_liste.append([datum,str_tag]+[el]+[jahr+"/"+k2,fach]+[datensatz[2]])
                            else:
                                gesamt_liste.append([datum,str_tag]+[el]+datensatz[1].split()+[datensatz[2]])
            datensatz = []
        akt_liste = []
        

for elem in gesamt_liste:
    print(elem)



