from .models import Chord
import os, re
import json
import unidecode, unicodedata
from html.parser import HTMLParser
import html

patt_ug_url = re.compile("\"(https?:\/\/tabs\.ultimate-guitar\.com\/tab.*)\"\n")

patt_crochets = re.compile("^\s*\[.*\]\s*$")
patt_rep = re.compile("(x\s?\d|\d\s?x)")
patt_tab = re.compile("(?:E|A|D|G|B|e)\s?\|\s?(?:.+?)-(?:.+?)$")
patt_song_part = re.compile("^(\s*\[?\s*(intro|verse|chorus|bridge|pont|couplet|refrain|interlude|instrumental|pre-chorus|outro|end|coda|transition|riff|solo)\s*\d?\s*\]?\s*:?\s*\]?)(.*)$", re.IGNORECASE)

chord = "([A-G](?:b|#)?(?:m|maj)?\d{0,2}(?:add)?(?:sus)?(?:dim)?(?:aug)?\d{0,2}(?:\s*/\s*\S+)?)"
patt_chord_lost = re.compile("\s"+chord+"\s")

patt_chord = re.compile("\[ch\](.+?)\[\/ch\]")
patt_sharp_in_non_chord = re.compile("#(?![^\[ch\]]*\[\/ch\])")
patt_json_extract = re.compile("<script>\s*window.UGAPP.store.page\s=\s(.*);")
patt_json_extract_new = re.compile("<div\sclass=\"js-store\"\sdata-content=\"(.*)\"></div>")

patt_html_code = re.compile("(?:[^a-zA-Z0-9\s]#|&[^a-zA-Z0-9\s])(\d{1,4};)")

USER       = os.path.expanduser("~")
ROOTDIR    = os.path.dirname(os.path.realpath(__file__))
BOOKDIR    = os.path.join(ROOTDIR,"books")
WDIR       = os.path.join(ROOTDIR,"data")
TODODIR    = os.path.join(WDIR,"html")
EXTRACTDIR = os.path.join(WDIR,"txt")
# MANUDIR    = os.path.join(WDIR,"02edited-txt")
# DONEDIR    = os.path.join(ROOTDIR,"songs","00_auto_import_test")
DONEDIR    = os.path.join(WDIR,"sg")

if not os.path.exists(TODODIR):
    os.makedirs(TODODIR)
if not os.path.exists(EXTRACTDIR):
    os.makedirs(EXTRACTDIR)
if not os.path.exists(DONEDIR):
    os.makedirs(DONEDIR)

h = HTMLParser()

def is_empty(line):
    return line.strip() == ""

def is_only_chords_line(line):
    line, nb_sub = re.subn(patt_chord,"",line)
    return line.strip() == "" and nb_sub > 0

def has_chords_line(line):
    return re.search(patt_chord,line) != None

def is_song_part_header(line):
    return re.search(patt_song_part,line) != None

def is_tab_line(line):
    return re.search(patt_tab,line) != None


def import_from_ug():
    # print_box("Importing bookmarks")
    # print("- from Chromium : ")
    CHROMIUM_BOOKMARKS = os.path.join(USER,".config/chromium/Default/Bookmarks")
    # return [CHROMIUM_BOOKMARKS]
    imports = []
    new_import2db = []
    import_but_already_in_db = []
    new2db_but_already_imported = []
    errors_imports = []
    # errors_added2db = []
    if os.path.isfile(CHROMIUM_BOOKMARKS):
        fr = open(CHROMIUM_BOOKMARKS,"r")
        bookmarks = "\n".join(fr.readlines())
        fr.close()
        urls = re.findall(patt_ug_url, bookmarks)
        # print("Found {} Ultimate Guitar urls".format(len(urls)))
        cpt = 0
        for url in urls:
            if not os.path.isfile(os.path.join(TODODIR,os.path.basename(url))):
                # print(url)
                cmd = "wget -q -U firefox -P \"" + TODODIR + "\" \"" + url + "\""
                if os.system(cmd) != 0:
                    errors_imports.append(url)
                    continue
                else : 
                    imports.append(os.path.basename(url))

    return imports, errors_imports


def ug_old_import(j):
    artist = j["data"]["tab"]["artist_name"].replace("&","and")
    title = j["data"]["tab"]["song_name"].replace("&","and")
    try: capo = j["data"]["tab_view"]["meta"]["capo"]
    except: capo = -1
    content = j["data"]["tab_view"]["wiki_tab"]["content"],
    chords = ", ".join(list(j["data"]["tab_view"]["applicature"].keys()))

    return artist, title, capo, content, chords

def ug_new_import(j):
    artist = j["store"]["page"]["data"]["tab"]["artist_name"]
    title = j["store"]["page"]["data"]["tab"]["song_name"]
    try: capo = j["store"]["page"]["data"]["tab_view"]["meta"]["capo"]
    except: capo = -1
    content = j["store"]["page"]["data"]["tab_view"]["wiki_tab"]["content"].replace("[tab]", "").replace("[/tab]", "")
    chords = ", ".join(list(j["store"]["page"]["data"]["tab_view"]["applicature"].keys()))

    return artist, title, capo, content, chords


def add_to_db(imports=[]):
    new_to_db = []
    updated_in_db = []
    already_in_db = []
    duplicates = []
    errors = []
    for filename in os.listdir(TODODIR):
        fr = open(os.path.join(TODODIR, filename),"r")
        html2txt = "\n".join(fr.readlines())
        txt2json = re.findall(patt_json_extract, html2txt)

        ug_new_imported_tab = False

        if len(txt2json) == 1: # ug old format
            get_metadata = ug_old_import
        else :
            txt2json = re.findall(patt_json_extract_new, html2txt)
            if len(txt2json) != 1:
                errors.append(filename)
                continue
            # ug new format
            txt2json[0] = html.unescape(txt2json[0])
            get_metadata = ug_new_import
            ug_new_imported_tab = True

        j = json.loads(txt2json[0])
        fr.close()

        artist, title, capo, content, chords = get_metadata(j)

        try:
            chord = Chord.objects.get(artist=artist, title=title)
            if filename in imports: # if the html file has just been imported but the chord already exist (reimport), update the existing 
                if os.path.basename(chord.file.name) != filename:
                    duplicates.append( (chord.pk, os.path.basename(chord.file.name)) )                
                chord.artist=artist
                chord.title=title
                chord.capo=capo
                chord.edited=False
                chord.chords=chords
                chord.content=content
                chord.file=os.path.join(TODODIR, filename)
                chord.save()
                updated_in_db.append(chord.pk)
            else:    
                if os.path.basename(chord.file.name) != filename:
                    duplicates.append( (chord.pk, filename) )
                else:
                    already_in_db.append(chord.pk)
                # if ( chord.pk in already_in_db or chord.pk in new_to_db ) and chord.pk not in duplicates:
                    # print("chordfile = ", chord.file)
                    # print("filename = ", filename)
                    # duplicates.append(chord.pk)
        except Chord.DoesNotExist:
            chord = Chord( artist=artist,
                           title=title,
                           capo=capo,
                           nbcol=1,
                           edited=False,
                           chords=chords,
                           content=content,
                           file=os.path.join(TODODIR, filename))
            chord.save()
            new_to_db.append(chord.pk)

    return new_to_db, updated_in_db, list(set(already_in_db)), duplicates, errors

    # jout["lowtitle"] = unidecode.unidecode(jout["title"].lower().replace(" ","_"))
    # jout["lowartist"] = unidecode.unidecode(jout["artist"].lower().replace(" ","_"))

    # if not os.path.exists(os.path.join(EXTRACTDIR,jout["lowartist"],jout["lowtitle"])+".txt") or FORCE:
    #    # not os.path.exists(os.path.join(MANUDIR   ,jout["lowartist"],jout["lowtitle"])+".json"):
    #     if not os.path.exists(os.path.join(EXTRACTDIR,jout["lowartist"])):
    #         os.makedirs(os.path.join(EXTRACTDIR,jout["lowartist"]))
    #     print("==> {}{:.20}{}, {:.20}".format(color.BOLD, jout["artist"],color.END,jout["title"]))
    #     cpt += 1
        
    #     jout["nb_column"] = 1
    #     jout["edited"] = 0
    #     jout["chords"] = list(j["data"]["tab_view"]["applicature"].keys())
    #     # jout["d_chords"] = j["data"]["tab_view"]["applicature"]

    #     for chord in j["data"]["tab_view"]["applicature"]:
    #         if chord not in d_chords:
    #             d_chords[chord] = j["data"]["tab_view"]["applicature"][chord]

    #     fw = open(os.path.join(EXTRACTDIR,jout["lowartist"],jout["lowtitle"])+".txt","w")
        
    #     fw.write("[METADATA]\n")
    #     fw.write("title : {}\n".format(jout["title"].strip()))
    #     fw.write("artist : {}\n".format(jout["artist"].strip()))
    #     fw.write("lowtitle : {}\n".format(jout["lowtitle"].strip()))
    #     fw.write("lowartist : {}\n".format(jout["lowartist"].strip()))
    #     fw.write("capo : {}\n".format(jout["capo"]))
    #     fw.write("nb_column : {}\n".format(jout["nb_column"]))
    #     fw.write("chords : {}\n".format(jout["chords"]))
    #     fw.write("edited : {}\n".format(jout["edited"]))
    #     fw.write("[ENDMETADATA]\n")

def clean_odd_or_even_line_breaks(chord):
    lcontent = chord.content.rstrip().split('\n')

    DEL_ODD = True
    DEL_EVEN = True
    i = 0
    while i < len(lcontent)-1:
        if DEL_EVEN and i%2 == 0:
            if not is_empty(lcontent[i]):
                DEL_EVEN = False
            
        if DEL_ODD and i%2 == 1:
            if not is_empty(lcontent[i]):
                DEL_ODD = False

        if not DEL_EVEN and not DEL_ODD:
            break

        i += 1

    if DEL_EVEN or DEL_ODD and not (DEL_EVEN and DEL_ODD): # xor
        lcontent_new = []
        i = int(DEL_EVEN)
        while i < len(lcontent):
            lcontent_new.append(lcontent[i])
            i += 2

        lcontent = lcontent_new

    chord.content = '\n'.join(lcontent)

def clean_multiple_line_breaks(chord):
    # Remove multiple line break
    lcontent = chord.content.rstrip().split('\n')

    i = 0
    lcontent_new = []
    while i < len(lcontent):
        if not (i+1 < len(lcontent) and is_empty(lcontent[i].strip()) and is_empty(lcontent[i+1].strip())):
            lcontent_new.append(lcontent[i])
        i += 1
    lcontent = lcontent_new

    chord.content = '\n'.join(lcontent)

def clean_empty_lines_at_begin_and_end(chord):
    lcontent = chord.content.split('\n')

    i = 0
    while i < len(lcontent):
        if not is_empty(lcontent[i]):
            break
        i += 1

    j = len(lcontent) - 1
    while j >= 0:
        if not is_empty(lcontent[j]):
            break
        j -= 1

    chord.content = '\n'.join(lcontent[i:j+1])

def clean_chord(chord_id):
    chord = Chord.objects.get(pk=chord_id)
    clean_odd_or_even_line_breaks(chord)
    clean_multiple_line_breaks(chord)
    clean_empty_lines_at_begin_and_end(chord)

    warning_lines = []
    removed_content_confirmation = []

    lcontent = chord.content.rstrip().split('\n')

    # Find begining and trash everything before
    i=0
    while i < len(lcontent):
        if (has_chords_line(lcontent[i]) or is_song_part_header(lcontent[i]) or is_tab_line(lcontent[i]) or re.search(patt_crochets,lcontent[i]) != None) : 
            break
        i += 1

    if i < len(lcontent) and i >= 1 and not is_empty(lcontent[i].strip()):
        removed_content_confirmation.extend(list(range(i)))

    while i < len(lcontent):            
        # Fix encoding - Bad character
        if "\\" in lcontent[i]:
            lcontent[i] = lcontent[i].replace('\\',' ')

        # Replace html character
        if re.search(patt_html_code, lcontent[i]) != None :
            lcontent[i] = unicodedata.normalize('NFC',h.unescape(re.sub(patt_html_code,r'&#\1',lcontent[i])))

        # Sharp in line (not a chord)
        if re.search(patt_sharp_in_non_chord, lcontent[i]) != None :
            lcontent[i] = re.sub(patt_sharp_in_non_chord, '\#', lcontent[i])
            warning_lines.append(i)

        #Encoding failure prevention
        j = 0
        while(j < len(lcontent[i])):
            if(ord(lcontent[i][j])>256 or ord(lcontent[i][j]) == 147):
                lcontent[i] = lcontent[i][:j]+unidecode.unidecode(lcontent[i][j])+lcontent[i][j+1:]
            j += 1

        # Remove chords in parenthesis and add whitspaces instead
        if(re.search("(\(.+?\))",lcontent[i]) and has_chords_line(lcontent[i])):
            # print("before = ", lcontent[i])
            lcontent[i] = re.sub("(\(.+?\))", lambda match:' '*len(re.sub(patt_chord, r'\1', match.group(1))), lcontent[i]).rstrip()
            # print("after = ", lcontent[i])

        # Remove repetition pattern i.e "x2" or "4 x"
        if(re.search(patt_rep, lcontent[i])):
            lcontent[i] = re.sub(patt_rep, "", lcontent[i])

        # The line has chords, but not only
        if(has_chords_line(lcontent[i]) and not is_only_chords_line(lcontent[i])): 
            if is_song_part_header(lcontent[i]):
                lcontent[i] = re.sub(patt_song_part, r'\1\n\3', lcontent[i]).rstrip()

            relicate = re.sub('[^a-zA-Z0-9\s]', '',re.sub(patt_chord, "", lcontent[i]))
            warning_lines.append(i)
            if(is_empty(relicate)):
                chords_found = re.findall(patt_chord, lcontent[i]) 
                indices_chords_found = [m.start() for m in re.finditer(patt_chord, lcontent[i])]
                new_line = ""
                for idx, x in enumerate(indices_chords_found):
                    new_line += ' '*(x - len(new_line))
                    new_line += "[ch]"+ chords_found[idx] +"[/ch]"
                lcontent[i] = new_line #re.sub(patt_chord, r'\[\1]', new_line)
                # continue
            # elif(re.findall(patt_chord_lost, relicate) != []):
                # warning_lines.append(i)
                # Some lost chords without tag
                # print(color.YELLOW, "Lost chords : ", relicate.strip(), color.END)
                # jsonlog["optional"][filename][i+line_nb][len(jsonlog["optional"][filename][i+line_nb].keys())] = {"content":lcontent[i],"reason":"lost-chord"}
            # else:
            #     removed_content_confirmation.append(i)
            #     i += 1
            #     continue
            #     # Most likely junk
            #     print("Delete line : ", lcontent[i].strip())
            #     jsonlog["optional"][filename][i+line_nb][len(jsonlog["optional"][filename][i+line_nb].keys())] = {"content":lcontent[i],"reason":"junk"}
        i += 1
        # fw.write(lcontent[i])
        # fw.write('\n')


    # if removed_content_confirmation != "":
    chord.removed_content_confirmation = ", ".join(map(str, removed_content_confirmation))
    # if warning_lines:
    chord.warning_lines = ", ".join(map(str, warning_lines))
    chord.content = '\n'.join(lcontent)
    chord.save()
    # fw.close()

def update_all(): # import html files from UG chromium bookmarks
    imports, errors_imports = import_from_ug()

    new_to_db, updated_in_db, already_in_db, duplicates, errors_add_to_db = add_to_db(imports)

    for chord in Chord.objects.all():
        clean_chord(chord.pk)
    # for url in urls:
    #     if url in errors_imports :
    #         continue
    #     pkid, new2db = add_to_db(os.path.basename(url))
    #     if url in imports:
    #         if new2db:
    #             new_import2db.append(pkid)
    #         else:
    #             import_but_already_in_db.append(pkid)
    #     else:
    #         if new2db:
    #             new2db_but_already_imported.append(pkid)
    #         # else:
    #         #     errors_added2db.append(url)

    return {"new_to_db" : new_to_db,
            "updated_in_db" : updated_in_db,
            "already_in_db" : already_in_db,
            "duplicates" : duplicates,
            "errors_add_to_db" : errors_add_to_db,
            "imports" : imports,
            "errors_imports" : errors_imports}
                # "errors_added2db" : errors_added2db}
        # return {"imports" : imports, "added2db" : added2db, "errors" : errors}
    #     print("{}Successfull{}".format(color.GREEN, color.END))
    # else:
    #     print(CHROMIUM_BOOKMARKS, "doesn't exist, nothing was imported")

def format_content(content):
    return content.replace("[ch]", "<b>").replace("[/ch]", "</b>")