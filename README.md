# ArcheVP

- **[Über ArcheVP](#about)**
- **[Bedienung](#bedienung)**
- **[Verfügbare Kommandos](#commands)**
- **[Beispielkonfiguration](#example)**

This Bot does not make sense in English, except you only speak English on Archenhold-Gymnasium Berlin-Schoeneweide. This does not make sense since lessons are only taught in German there. Sorry :|

<a id="about"></a>
### Über ArcheVP

Der ArcheVP-Bot (@archevp_bot, https://telegram.me/archevp_bot) bringt dir (sobald er fertiggestellt ist) stets bei Bekanntmachung deinen neuen Vertretungsplan. Gib einfach deinen URL und deine Kurse (Klassen) ein und du wirst staunen – du bist stets über den aktuellen Vertretungsplan informiert. ;)

Der Bot nutzt die [Telepot-API.](https://github.com/nickoala/telepot)

<a id="bedienung"></a>
### Bedienung

Mit `/help` kannst du dir alle verfügbaren Kommandos mit einer kurzen Erklärung anzeigen lassen.

Wenn du deinen aktuellen Vertretungsplan ansehen willst, gib einfach `/vp` ein.

Damit du diesen ansehen kannst, musst du allerdings ein paar Einstellungen vornehmen. Tippe erst `/add` ein, um deine Kurse oder Klassen, die du sehen möchtest, hinzuzufügen. Tippe dann `/url` ein, um deinen persönlichen Link zum Vertretungsplan anzugeben. Diesen findest du [auf der Schulseite](http://pi.archenhold.de/service/vertretungsplan) bei „Zugangscode auf andere Geräte übertragen“ (ob mobil, oder Web ist egal), sobald du dich angemeldet hast.

Damit bist du schon fertig. Deine eingegebenen Kurse oder Klassen kannst du dir nun mit `/info` anzeigen lassen.

<a id="commands"></a>
### Verfügbare Kommandos

- /help (zeigt die Hilfe an)
- /vp (zeigt deinen persönlichen, aktuellen Vertretungsplan an)
- /info (zeigt deine eingetragenen Kurse/Klassen an)
- /url (setzt deinen Link zum Vertretungsplan)
- /add (fügt Kurse/Klassen zu deinen Kursen/Klassen hinzu)
- /del (löscht einzelne Kurse/Klassen)

<a id="example"></a>
### Beispielkonfiguration

```
/url http://pi.archenhold.de/service/vertretungsplan?sid=2TyWg0cuvzTPAoILD6dhLUB1TpSJnWHQ
/add 9/1, 9 WEn, 9 WIn
```

```
/url http://m.archenhold.de/service/vertretungsplan?sid=2TyWg0cuvzTPAoILD6dhLUB1TpSJnWHQ
/add L09, L18, G27, G36, G45, G54, G63, G72, G81, G90, Q1
```
