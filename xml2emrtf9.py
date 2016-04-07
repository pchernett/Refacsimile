#!/usr/bin/python
# coding=latin1
# Coding needed because of pound sign
import xml.etree.ElementTree as ET
import logging
from objectdefs9 import *
from optparse import OptionParser
import sys
from PyQt4 import QtCore, QtGui, QtWebKit
from PyQt4.QtCore import pyqtSlot

#Version 0.9
# Copes with xml files with no clef sign set (Musescore style). 
# Double bar after close repeat at end.
# Accidentals table now correctly updated after a key change. 
# Corrected placement of flats in keysigs for C clefs. 
# Added an option to choose between the two "G" (treble) clefs. Option -g (--ganassi_treble)
# A work around for a MS bug precede a line end or page break with a font change to a "normal" font. 
# Add option to print text in JSL Blackletter. Option -a (--alt_textfont)
# Add rudimentary option to print all the words out at the end of each part.
# Remove "Default Composer".
# Default to an accidental on every note it applies to.
# Detects and corrects orphan end repeat at beginning of line.
#Version 0.8
# Consistent handling of dotted and tied notes (eg if a dotted note is tied)
# Redesigned handling of clefs, key and time sigs to allow inline changes.
# Corrected bug in whole bars rests
# Multiple rests collapsed to smallest number of printable rests
# Multiple bar rests collapsed
# CL option to apply accidental only to first note of a sequence at same pitch
# Inline changes of time, key and clef
# Support for movable C clefs
# Repeats
#Version 0.7
# Corrected bug with semiquaver restds
# Corrected bug in positioning notes on bass clef
# Use semiquaver font for all rests (works best on my system)
# Version 0.6
# Convert lyric syllables & titles from UTF-16 to Latin-1
# Add support for quaver rests
# Improve handling of rests eg whole bars in 3-time measures
# Version 0.05
# Sorted problem with ties
# Fixed bug with semiquavers
# Option to break lines by note count
# F5 clef for treble-8 parts
# version 0.04
# First fully working version		

#### What should work:
# - parsing partwise XML files
# - notes
# - rests
# - whole bar's rest
# - dotted notes	
# - ties
# - tied notes converted to dotted notes
# - treble, tenor, bass clefs (including inline clef changes)
# - F clef on top line for octave treble parts
# - C clefs on lines 1,2,3,4,5
# - time signatures (including inline time sig changes)	
# - key signatures (including inline changes)
# - Accidentals
# - Lyrics
# - Repeats
# - Line breaking by counting numbers of bars or numbers of notes/rests (selectable by command line)
###################################################################

# Note on key signatures, time signatures and clefs, so I don't forget.
# These can change inline and, in xml, appear in an "attributes"
# tag. Within this tag, they can appear in any order but,
# conventionally, they appear in the order: clef, key, time.
# The program reads the music data twice: first it parses the xml
# into a list of events, then it parses the event list and outputs
# the rtf. The current clef, key and time are not needed during the
# xml parsing, but they are used when the events are parsed. 
# eg the current key sig is needed for accidentals. Current values
# are tracked by attributes of the voice object. When we encounter
# a 'clef', 'key, or 'time' event, we set up the new values,
# temporarily, in another set of voice attributes: new_clef,
# new_key, new_m1, new_m2 (for meter). These events are always
# followed by an "attribute_end" event. When this is encountered,
# the new attributes are compared with existing ones and an rtf
# string is formed with the attributes in the correct cklef, key,
# time order. Fro this to work correctly, the attributes in the
# voice objects must have been initialised to null values at voice
# creation.
#############################################################################
#
#              XML Parser functions
#
#############################################################################

            
def process_pitch(element):
    step = 0
    octave = 0
    modifier = 0
    for e in element:
        if e.tag == "step":
            step = e.text
        elif e.tag == "octave":
            octave= e.text
        elif e.tag == "alter":
            modifier = e.text
    logging.debug( "Processing pitch. Step: " + step + "; Octave: " + str(octave) + "; Modifier: " + str(modifier))
    return [convert_pitch(step,octave), modifier]
        
def process_note(element):
    pitch = 0		# Pitch number of note with 0 = C1
    modifier = 0	# +/-1 for accidentals; "rest" for a rest
    duration = 0	# coded duration number
    tied = False
    dot = False
    syllabic_type = "" #single, etc
    text = ""
    
    for e in element:
        if e.tag == "pitch":
            [pitch, modifier] = process_pitch(e)
        if e.tag == "type":
            duration = process_type(e)
        if e.tag == "notations":
            for ee in e:
                if ee.tag =="tied":
                    if ee.attrib["type"] == "start":
                        logging.debug("Start of tie detected")
                        tied = True
        if e.tag == "tie":
            if e.attrib["type"] == "start":
                logging.debug("Start of tie detected")
                tied = True
        if e.tag == "dot":
            dot = True
        if e.tag == "rest":
            modifier = "rest"
            try:
                if e.attrib["measure"] == "yes":
                    modifier = "barrest"
            except:
                pass
        if e.tag == "lyric":
            [syllabic_type, text] = process_lyric(e)
    logging.debug("Processing note: Pitch: " + str(pitch) + "; duration: " + str(duration) + "; modifier: " + str(modifier))
    if dot == True:
        duration = 3*duration/2
    return [pitch, modifier, duration, tied, syllabic_type, text]

def utf2latin(string):
    if not string:
        return ""
    l=""
    for c in string:
        try:
            c=c.encode('latin-1')
        except:
            c="?"
        l+=c
    return l
    
def process_lyric(element):
    syllabic_type = "single"
    lyric = 0
    for e in element:
        if e.tag == "syllabic":
            syllabic_type = e.text
        if e.tag == "text":
            lyric = e.text
            lyric = utf2latin(lyric)
    return [syllabic_type, lyric]
    
def process_type(element):
    types = {"maxima" :1, "long": 2, "longa":2, "breve": 4, "whole": 8, "half": 16, "quarter": 32, "eighth": 64, "8th": 64, "16th": 128, "32nd": 256, "64th": 512, "128th": 1024}
    try:
        t = types[element.text]
        l = 4096/t
    except:
        logging.warn ("Unknown note length: " + element.text)
        l = 0
    return l

def process_clef(element):
    sign = "G"
    line = 2
    clef_octave_change = 0
    for e in element:
        if e.tag == "sign":
            sign = e.text
        elif e.tag == "line":
            line = e.text
        elif e.tag == "clef-octave-change":
            clef_octave_change = e.text
    return [sign, line, clef_octave_change]

def process_attributes(element, voice):
    barrest_length=0
    change_of_clef_key_or_time = False
    for e in element:
        if e.tag == "clef":
            [sign, line, clef_octave_change] = process_clef(e)
            voice.append_event("clef", sign, 0, clef_octave_change, line)
            logging.debug("Updating clef " + sign + ", line " + str(line) + ", octave change " + str(clef_octave_change))
            change_of_clef_key_or_time = True
        if e.tag == "key":
            [fifths, mode] = process_key(e)
            voice.append_event("key", mode, 0,0, fifths)
            logging.debug("Setting key to " + str(fifths) + " " + mode)
            change_of_clef_key_or_time = True
        if e.tag == "time":
            [beats, beat_type] = process_time(e)
            voice.append_event("time", 0, beat_type, 0, beats)
            logging.debug("Setting time sig to " + beats + "/" + beat_type)
            change_of_clef_key_or_time = True
        #if e.tag == "measure-style":
        #	for ee in e:
        #		if ee.tag =="multiple-rest":
        #			barrest_length = int(ee.text)
    if change_of_clef_key_or_time:
        voice.append_event("attribute_end", 0, 0, 0, 0)
    #return barrest_length
def process_time(element):
    beats = 0
    beat_type = 0
    for e in element:
        if e.tag == "beats":
            beats = e.text
        elif e.tag == "beat-type":
            beat_type = e.text
    return [beats, beat_type]

def process_key(element):
    key = 0
    mode = ""
    for e in element:
        if e.tag =="fifths":
            key = e.text
        elif e.tag == "mode":
            mode = e.text
    return [key, mode]
        
def process_partlist(element,tune):
    for elem in element:
        if elem.tag == "score-part":
            process_scorepart(elem,tune)
            
def process_scorepart(element,tune):
    logging.debug("Process_scorepart")
    part_id = element.attrib['id']

    if part_id in tune.voicelist:
        newvoice = tune.voicelist[part_id]
        logging.debug("Scorepart id already exists")
    else:
        newvoice = voicedata(tune)		# Create a new voice object
        tune.voicelist[part_id] = newvoice
        tune.voice_sequence.append(part_id)
        logging.debug("Scorepart creating new voice.")
    for e in element:
        if e.tag == 'part-name':
            if e.text:
                newvoice.name = e.text		
    logging.debug("Processing scorepart "+ part_id + ": " + newvoice.name)


def process_part(element,tune):
    try:
        dummy = element.attrib['id']
    except:
        logging.fatal("Part with no id in xml")
        exit()
    logging.debug ("Processing voice "+ element.attrib['id'])
    try:
        this_voice = tune.voicelist[element.attrib['id']]
        for e in element:
            if e.tag == "measure":
                process_measure(e, this_voice)
    except:
        pass
        #ID in list, but no corresponding part
            
def process_barline(element,voice):
    repeat_type = ""
    for e in element:
        if e.tag == "repeat":
            try:
                repeat_type= e.attrib["direction"]
            except:
                pass
            if repeat_type =="forward":
                voice.append_event("start_repeat", 0,0,0,0)
            elif repeat_type == "backward":
                voice.append_event("end_repeat", 0,0,0,0)			

def process_measure(element, this_voice):
    logging.debug ("Processing measure" + element.attrib['number'])
    #barrest_length=1
    for e in element:

        if e.tag =="note":
            [pitch, modifier, duration, tied,  syllabic_type, text] = process_note(e)
            this_voice.add_syllable(syllabic_type, text)
            logging.debug("Note: "+ str(pitch) + "; " + str(modifier) + "; " + str(duration))
            if modifier == "rest": # Note is a rest
                if duration:
                    this_voice.append_event("rest", pitch, duration, "", "")
                else:
                    #It must be a whole bar rest
                    this_voice.append_event("barrest", 0, 1,0, "")
            elif modifier == "barrest":
                this_voice.append_event("barrest", 0, 1, 0, "")
            elif this_voice.tie:
                this_voice.extend_last_note(duration)
                this_voice.tie = False
            else:
                this_voice.append_event("note", pitch, duration, modifier, "")
            if tied and (duration >=0):
                this_voice.tie = True
        elif e.tag == "attributes":
            #barrest_length = process_attributes(e, this_voice)
            process_attributes(e, this_voice)
        elif e.tag == "barline":
            process_barline(e,this_voice)
        
    this_voice.check_bars()

def process_identification(element, tune):
    for e in element:
        if e.tag == "creator":
            if e.attrib["type"] == "composer":
                tune.composer = e.text
    
#######################################################################
#
#          Other functions
#
#######################################################################

        
def convert_pitch(s,o):
    #Assign note a number starting from C in octave 1
    sequence = ["C","D","E","F","G","A","B"]
    if s in sequence:
        n= sequence.index(s) + 7*(int(o)-1)
    else:
        logging.critical("Unrecognised note in convert_pitch")
    return n		
        
def make_note (voice,note, length,accidental, middle):
    char_table = ['M','N','C','D','E','F','G','A','b','c','d','e','f','g','a','m','n']
    # These are the notes in Paul's font from two leger lines below to 
    # two above the staff
    # ie an index of '8' (the character 'b') represents a note in the middle of the staff
    
    # Check if accidental needed
    #print accidental
    font_object = The_font_object;
    accidental = voice.check_accidental(note,int(accidental))
    position = note-middle+8
    if position not in range(len(char_table)):
        logging.debug ("Note "+ str(note) + " out of range in function make_note.")
        return "+"
    font = ''
    # Check notes for >= to expected length to allow for dotted notes
    remainder = length
    if length > 4000:
        logging.warning ("Note too long to be displayed")
        return "+"
    elif length >= 2048:
        font = font_object.make_fontstring("longfont")	
        remainder -= 2048
    elif length >= 1024:
        font=font_object.make_fontstring("brevefont")
        remainder -= 1024
    elif length >= 512:
        font= font_object.make_fontstring("semibrevefont")
        remainder -= 512
    elif length >= 256:
        font = font_object.make_fontstring("minimfont")
        remainder -=256
    elif length >= 128:
        font = font_object.make_fontstring("crotchetfont")
        remainder -= 128
    elif length >= 64:
        font = font_object.make_fontstring("quaverfont")
        remainder -= 64
    elif length >=32:
        font = font_object.make_fontstring("semiquaverfont")	
        remainder -= 32	
    else:
        logging.warning("Note too short to be displayed")
        return "+"
    dot = ''
    if (length%3 == 0):
        # Note lengths are only divisible by 3 in the case of a dotted note
        # so switch to the dot clef and print at the same position as the note
        dot =font_object.make_fontstring("dotsfont") + char_table[position]
        remainder -= (length-remainder)/2
    modifier=''
    if accidental==1:
        modifier = font_object.make_fontstring("sharpsfont") +char_table[position]
    if accidental==-1:
        modifier = font_object.make_fontstring("flatsfont") +char_table[position]
    if position in range(len(char_table)):
        extra_bit = ""
        if remainder>0:
            if options.single_accidentals:
                accidental = 0
            extra_bit = make_note (voice,note, remainder,accidental, middle)
        return modifier+font+char_table[position] + dot + extra_bit
    else:
        logging.warning ("Note found outside printable range. Note/Position: "+ str(note)+ str(position))
        return "+"

def make_rest (length):
    font_object = The_font_object;
    #Rests are [ 8, 4, 2, 1, 5] Long, breve, semibreve, minim, quaver rests
    rest=''
    while length >0:
        if length >= 2048:
            rest += '8'	
            length -= 2048
        elif length >= 1024:
            rest +='4'
            length -= 1024
        elif length >= 512:
            rest +='2'
            length -= 512
        elif length >= 256:
            rest +='1'
            length -= 256
        elif length >= 128:
            rest +='5'
            length -= 128
        elif length >=64:
            rest +='6'
            length -= 64
        else:
            logging.warning ("Rest too short to be displayed")
            length = 0
    return font_object.make_fontstring("crotchetfont") +rest 
    
def make_barrest(this_voice,n):
    m1 = int(this_voice.m1)
    m2 = int(this_voice.m2)
    beat = 512/m2
    logging.debug ("Bar rest of length " + str(n*beat*m1)+ " time: "+str(m1)+"/"+str(m2))
    return make_rest(n*beat*m1)
    
def print_key(voice, font_object):
    logging.debug ("Setting key sig for voice: "+ voice.name)
    key = voice.key
    logging.debug ("Key is " + str(key))
    clef=voice.clef
    if clef=="C" and not voice.clef_line ==3:
        clef = clef + str(voice.clef_line)
    keystring = font_object.get_key_string(clef,key)
    return keystring

def print_meter(voice, font_obj):
    return font_obj.get_meter(voice.m1)
    
def calculate_middle(clef,line,octave):
    middle =0
    line = int(line)
    octave=int(octave)
    if clef == "G" or clef =="treble":
        middle = convert_pitch("B",4)
    elif clef == "F" or clef == "bass":
        middle = convert_pitch("D",3)
    elif clef == "C":
        middle = convert_pitch("C",4) - 2*(line -3)
    middle += 7*int(octave)
    return middle

def process_XMLfile(filename, tune):
    status=0
    # Assume command line argument is an XML filename of the form: qwertyuiop.xml
    # More or less than one dot in the file name will upset the program!

    tree = ET.parse(filename)
    root = tree.getroot()
    
    if not root.tag == "score-partwise":
        logging.fatal("This software version will only decode MusicXML files in 'score-partwise' format'")
        exit()

    #if options.notecount:
    #    tune.maxchars = int(options.notecount)
    #    tune.newlinemode = "chars"
    #elif options.barcount:
    #    tune.maxbars = int(options.barcount)
    #    tune.newlinemode = "bars"
    #if options.single_accidentals:
    #    tune.single_accidentals = True
    #if options.ganassi_treble:
    #    font_object.clefsymbols["treble"] = "z"
    #    font_object.clefsymbols["G"] = "z"
    #if options.alt_text_font:
    #    font_object.fontlist["textfont"] = font_object.alt_text_font
    #    del font_object.fontnames[:] # Need to rebuild list of font names
    #    for font in font_object.fonttypes:
    #        font_object.fontnames.append(font_object.fontlist[font])

    for element in root:
        if element.tag == "part-list":
            process_partlist(element,tune)
        elif element.tag == "movement-title":
            tune.title = utf2latin(element.text)
            logging.debug ("Setting title to " + element.text)
        elif element.tag == "work":
            for e in element:
                if e.tag == "work-title":
                    tune.title = utf2latin(e.text)
        elif element.tag == "part":
            process_part(element,tune)
        elif element.tag == "identification":
            process_identification(element,tune)
            
    # Do some processing on the voice objects
    for this_voice, voice_ref in tune.voicelist.iteritems():
        i = 0
        while i < len(voice_ref.events) and voice_ref.events[-1] in ["newline", "start_noteline"]:
            voice_ref.events.pop()
            voice_ref.pitch.pop()
            voice_ref.lengths.pop()
            voice_ref.accidentals.pop()
            voice_ref.others.pop()
        if len(voice_ref.events)>0 and (not voice_ref.events[-1] == "endmark") and (not voice_ref.events[-1] == "end_repeat") and (not voice_ref.events[-1] == "lyricnewline"):
            voice_ref.append_event("endmark","",0,0,0)  #Add an endmark if one isn't present
            voice_ref.append_event("newline",0,0,0,0)
        if voice_ref.lyric_line:
            voice_ref.append_event("lyricline", 0, 0, 0, voice_ref.lyric_line)
        # Check for end repeat followed by start repeat and replace with mid repeat
        for index in range(len(voice_ref.events)-1):
            if voice_ref.events[index] == "end_repeat" and voice_ref.events[index+1] == "start_repeat":
                voice_ref.events[index]= "mid_repeat"
                voice_ref.events[index+1] = "null"
        # Check for sequences of rests
        for index in range(len(voice_ref.events)):
            if not (voice_ref.events[index]	== "rest"):
                continue
            i= index
            while (i<len(voice_ref.events)) and (voice_ref.events[i+1] == "rest"):
                voice_ref.lengths[index] += voice_ref.lengths[i+1]
                voice_ref.events[i+1] = "null"
                i +=1
        # and sequences of whole bar rests
        for index in range(len(voice_ref.events)):
            if not (voice_ref.events[index]	== "barrest"):
                continue
            i= index
            while (i<len(voice_ref.events)) and (voice_ref.events[i+1] == "barrest"):
                voice_ref.lengths[index] += voice_ref.lengths[i+1]
                voice_ref.events[i+1] = "null"
                i+=1

        # Check for end repeats at start of line
        for index in range(len(voice_ref.events)-2):
            if (voice_ref.events[index] == "newline" 
            and voice_ref.events[index+1] == "start_noteline"
            and voice_ref.events[index+2] == "end_repeat"):
                voice_ref.events[index] = "end_repeat"
                voice_ref.events[index+1] = "newline"
                voice_ref.events[index+2] = "start_noteline"
        #print voice_ref.events	
    return tune;

class Window(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout(self)
        self.button = QtGui.QPushButton('Select Files', self)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.handleButton)

    def handleButton(self):
        title = self.button.text()

        for path in QtGui.QFileDialog.getOpenFileNames(self, 
                         title, "\users\paul\Dropbox\Scores",
                        "XML files (*.xml)"):
            process_XMLfile(path, The_tune)
            create_RTF_from_XML(The_tune, path, The_font_object)


def create_RTF_from_XML(tune, path, font_object):
    status=0
    parts = path.split('.',1)	#Splits filename into 2 parts
    stem=parts[0]
    outfile = stem+".rtf"  
    #print font_object.fontlist	
    cli_parser = OptionParser(usage = "%prog [options] <xml file>", version="%prog Version: 0.9")

    cli_parser.add_option("-l", "--landscape",
        action="store_false", dest="portrait", default=False,
        help = "set page orientation to 'landscape' mode")
    cli_parser.add_option("-p", "--portrait",
        action="store_true", dest="portrait", default=False,
        help = "set page orientation to 'portrait' mode")
    cli_parser.add_option("-d", "--debug",
        action="store_true", dest="debug", default=False,
        help = "enable debugging mode: verbose messages sent to stderr")	
    cli_parser.add_option("-b", "--barcount", 
        action="store", type="string", dest="barcount",
        help = "select 'barcount' mode for line breaking and specify number of bars per line")
    cli_parser.add_option("-n","--notecount", 
        action="store", type="string", dest="notecount",
        help = "select 'notecount' mode for line breaking and specify number of notes per line")
    cli_parser.add_option("-s", "--single_accidentals", 
        action = "store_true", dest="single_accidentals", default=False,
        help="prints a single accidental at the start of sequences of notes at the same pitch")
    cli_parser.add_option("-o", "--omit_partnames",
        action="store_true", dest="omit_partnames", default=False,
        help="omit partnames from output file")
    cli_parser.add_option("-g", "--ganassi_treble",
        action = "store_true", dest="ganassi_treble", default=False,
        help="select Ganassi-style treble clef instead of default Morley style")
    cli_parser.add_option("-a", "--alt_text_font", 
        action = "store_true", dest = "alt_text_font", default = False,
        help = "select alternative text font JSL Blackletter instead of default JSL Ancient")
    cli_parser.add_option("-w", "--words_at_end",
        action= "store_true", dest="words_at_end",
        help="words (to a song) are printed at the end of each part")

    (options, args) = cli_parser.parse_args()

    rtf_file = rtf(outfile, font_object, options)
    #Tune may have one voice, probably not specifically named, or multiple voices
    multivoice=True
    logging.debug ("No of voices: "+ str(len(tune.voicelist)))
    no_of_voices = len(tune.voicelist)
    voice_count=0
    if no_of_voices < 2:
        multivoice = False
    for this_voice in tune.voice_sequence:
        voice_ref = tune.voicelist[this_voice]
        voice_count += 1
        logging.debug ("Title: " + tune.title)
        rtf_file.print_para('h',tune.title)
        rtf_file.print_para('c', tune.composer)
        if multivoice:
            logging.debug ("Voice: " + voice_ref.name)
            if not options.omit_partnames:
                rtf_file.print_para('s', voice_ref.name)
        out_string = rtf_file.note_style

        for i, (e, n, l, a, o) in enumerate(zip(voice_ref.events,voice_ref.pitch, voice_ref.lengths, voice_ref.accidentals, voice_ref.others)):
            if e=='note':	
                out_string += make_note(voice_ref,n,l,a, voice_ref.middle)
            elif e =='endmark':
                out_string 	+= ']'
            elif e=='rest':
                out_string += make_rest(l)
            elif e == "barrest":
                out_string += make_barrest(voice_ref,l)
            elif e == "lyricline":
                out_string += font_object.make_fontstring("textfont")
                out_string += "\\fs30"
                out_string += o	
                #out_string += font_object.make_fontstring("minimfont")
                out_string += "\\fs96"
                out_string += '\\line '
            elif e == 'clef':
                # e,n,l,a,o = "key", sign, 0 , octave, line
                voice_ref.new_clef = n
                voice_ref.new_clef_octave = a
                voice_ref.new_clef_line = o
                voice_ref.new_middle = calculate_middle(n, o,a)

            elif e == "key":
                # e, n, l, a, o = "key", mode, 0, 0, fifths
                voice_ref.new_key = int(o)
                voice_ref.new_mode = n
            elif e == 'time':
                voice_ref.new_m2 = int(l)
                voice_ref.new_m1 = int(o)
            elif e == "attribute_end":
                if voice_ref.new_middle==0:
                    #No clef is set
                    voice_ref.new_clef = "G"
                    voice_ref.new_clef_octave = 0
                    voice_ref.new_clef_line = 2
                    voice_ref.new_middle = calculate_middle("G", 2,0)
                if not (voice_ref.new_middle == voice_ref.middle):
                    # That means the clef has changed
                    voice_ref.middle = voice_ref.new_middle
                    voice_ref.clef = voice_ref.new_clef
                    voice_ref.clef_octave = voice_ref.new_clef_octave
                    voice_ref.clef_line = voice_ref.new_clef_line
                    #out_string += get_clef_symbol(voice_ref,font_object)
                    out_string += font_object.make_fontstring("minimfont")
                    out_string += font_object.get_clef(voice_ref.clef, voice_ref.clef_line, voice_ref.clef_octave)
                if not (voice_ref.key == voice_ref.new_key):
                    # Key sig has changed
                    #print voice_ref.key, voice_ref.new_key
                    voice_ref.set_keysig(voice_ref.new_key, voice_ref.new_mode)
                    out_string += print_key(voice_ref, font_object)

                if not ((voice_ref.m1 == voice_ref.new_m1) and (voice_ref.m2 == voice_ref.new_m2)):
                    #Time sig has changed
                    voice_ref.m1 = voice_ref.new_m1
                    voice_ref.m2 = voice_ref.new_m2
                    out_string += print_meter(voice_ref, font_object)	
            elif e == "newline":
                # Need to consider if this is the final line with notes in, we don't want a direct. 
                # Otherwise we must find the next note event and make a direct
                finished= False
                j = i
                while not finished:
                #Check if there is a following note line, as we need a direct
                    j+=1
                    if j >= len(voice_ref.events):
                        logging.debug ("EOL with no following note")
                        finished=True
                    else:
                        if voice_ref.events[j] == 'note':
                            out_string += font_object.make_direct(voice_ref.pitch[j], voice_ref)
                            logging.debug ("EOL, position " + str(i)+ ", followed, at position "+str(j)+ ", by note "+ str(voice_ref.pitch[j]))
                            finished=True
                out_string += font_object.make_fontstring("textfont")
                out_string += "\\line "
            elif e == "start_noteline":
                #out_string += get_clef_symbol(voice_ref,font_object)
                out_string += font_object.make_fontstring("minimfont")
                out_string += font_object.get_clef(voice_ref.clef, voice_ref.clef_line, voice_ref.clef_octave)
                out_string += print_key(voice_ref, font_object)
            elif e == "start_repeat":
                out_string += "("
            elif e == "end_repeat":
                out_string += ")"
            elif e == "mid_repeat":
                out_string += "R"
        rtf_file.print_para('g',out_string)
        if options.words_at_end:
            out_string = rtf_file.lyric_style
            #out_string += "Lyrics:\\line "
            out_string += voice_ref.all_lyrics
            rtf_file.print_para('g',out_string)
        if not voice_count == no_of_voices:
            rtf_file.print_para("g", "\\page")
    rtf_file.close()

    for v_id in tune.voice_sequence:
        v = tune.voicelist[v_id]
        #print "Event list:"
        #print zip(tune.voicelist[v_id].events, tune.voicelist[v_id].pitch, tune.voicelist[v_id].lengths, tune.voicelist[v_id].accidentals, tune.voicelist[v_id].others)
    
        return status


def get_options():
    cli_parser = OptionParser(usage = "%prog [options] <xml file>", version="%prog Version: 0.9")

    cli_parser.add_option("-l", "--landscape",
        action="store_false", dest="portrait", default=False,
        help = "set page orientation to 'landscape' mode")
    cli_parser.add_option("-p", "--portrait",
        action="store_true", dest="portrait", default=False,
        help = "set page orientation to 'portrait' mode")
    cli_parser.add_option("-d", "--debug",
        action="store_true", dest="debug", default=False,
        help = "enable debugging mode: verbose messages sent to stderr")	
    cli_parser.add_option("-b", "--barcount", 
        action="store", type="string", dest="barcount",
        help = "select 'barcount' mode for line breaking and specify number of bars per line")
    cli_parser.add_option("-n","--notecount", 
        action="store", type="string", dest="notecount",
        help = "select 'notecount' mode for line breaking and specify number of notes per line")
    cli_parser.add_option("-s", "--single_accidentals", 
        action = "store_true", dest="single_accidentals", default=False,
        help="prints a single accidental at the start of sequences of notes at the same pitch")
    cli_parser.add_option("-o", "--omit_partnames",
        action="store_true", dest="omit_partnames", default=False,
        help="omit partnames from output file")
    cli_parser.add_option("-g", "--ganassi_treble",
        action = "store_true", dest="ganassi_treble", default=False,
        help="select Ganassi-style treble clef instead of default Morley style")
    cli_parser.add_option("-a", "--alt_text_font", 
        action = "store_true", dest = "alt_text_font", default = False,
        help = "select alternative text font JSL Blackletter instead of default JSL Ancient")
    cli_parser.add_option("-w", "--words_at_end",
        action= "store_true", dest="words_at_end",
        help="words (to a song) are printed at the end of each part")

    (options, args) = cli_parser.parse_args()


###############################################################################
####################### Main Program starts here ##############################
###############################################################################
#usage = "%usage: %prog <xml file> [options]"

import sys
from PyQt4.QtGui import *

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    The_tune = tunedata()	# Create one instance of the tune object
    The_font_object = fontdata_class() # And one istance of fontdata

    The_window = Window()
    The_window.show()
    sys.exit(app.exec_())



#if options.debug:
#    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')	
#    pass
#else:
#    logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

