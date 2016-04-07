# coding=latin1
# Coding needed because of pound sign
import logging

class rtf():
	"""The RTF class is used to create instances of rtf files"""
	font_table = []
	musicfontsize = 96
	lyricfontsize= 30
	rtf_preamble = '{\\rtf1\\ansi\deff0{\\fonttbl'
	rtf_postamble = "\n}"
	orientation = "\landscape\n"
	dimensions = "\paperw15840\paperh12240\margl720\margr720\margt720\margb720\n"
	header_style =   "\\qc  \\b\\f0\\fs40" # Centred, bold, font zero in table, size 20pt
	composer_style = "\\qr \\f0\\fs30"	   # Right ailgned, 15 point
	subheader_style = "\\li1000\\ri1000 \\f0\\fs24" # Set L & R margins, font size 12
	note_style = "\\ql \\f1\\fs96 "
	general_style = '\\f1\\fs96'
	def __init__(self, filename, fontobj,opts):
		if opts.portrait:
			self.orientation =""
			self.dimensions = "\paperw12240\paperh15840\margl720\margr720\margt720\margb720\n"
		self.font_table = fontobj.fontnames[:]
		self.musicfontsize = 2* fontobj.musicfontsize
		self.general_style = '\\f1\\fs' + str(self.musicfontsize)
		self.lyric_style = '\\f0\\fs' + str(self.lyricfontsize)
		self.note_style = '\\ql \\f1\\fs' + str(self.musicfontsize) + " "
		self.handle = open(filename, 'w')
		self.handle.write(self.rtf_preamble)
		for index, font in enumerate(self.font_table):
			self.handle.write("{\\f" + str(index) + " " + font + ";}\n")
		self.handle.write("}\n")    # End of RTF header stuff
		self.handle.write(self.orientation)
		self.handle.write(self.dimensions)
		self.styles = {'h': self.header_style, 'c': self.composer_style, 's': self.subheader_style, 'n': self.note_style, 
			'g': self.general_style}	
	def print_para(self, style, stuff):
		# Writes a paragraph to rtf file
		try:
			style = self.styles[style]
		except:
			style = ''
		self.handle.write("{\\pard " + style + " " + stuff + "\n\\par}")
	def close(self):
		self.handle.write(self.rtf_postamble)
		self.handle.close()

class fontdata_class:
	"""
	The class 'fontdata_class'  holds information about fonts 
	and (potentially in the future) their sizes. We only instantiate one instance 	
	('fontdata') of this class
	"""
	fontlist = {"textfont": 'JSL Ancient', "longfont": 'EMLong',
		"brevefont":'EMbreve', "semibrevefont": 'EMSemibreve',
		"minimfont": 'EMMinim', "crotchetfont" : 'EMCrotchet',
		"quaverfont": 'EMQuaver',"semiquaverfont" : "EMSemiQuaver", "sharpsfont": 'EMSharps',
		"flatsfont": 'EMFlats', "directfont": "EMDirect",
		"dotsfont":'EMDots'}
	fonttypes = ["textfont", "longfont", "brevefont", "semibrevefont",
		"minimfont", "crotchetfont", "quaverfont","semiquaverfont", "sharpsfont",
		"flatsfont", "directfont", "dotsfont"]
	fontnames = []
	alt_text_font = "JSL Blackletter"
	musicfontsize =48
	char_table = ['M','N','C','D','E','F','G','A','b','c','d','e','f','g','a','m','n']
	# These are the notes in Paul's font from one leger line below to 
	# one above the staff
	# They correspond to my note positions from -8 to +8
	clefsymbols = {"bass": "x", "F": "x", "alto":chr(163), "C": chr(163), "C3": chr(163), "treble-8": "X",
		"treble": "Z", "G": "Z", "C1": "!", "C2":chr(34), "C4": "$", "C5":"%"}	
	def __init__(self):
		#try:
		#	with open(configfile) as fontspec:
		#		for dataline in fontspec:
		#			itemlist = shlex.split(dataline)
		#			if len(itemlist) < 2:
		#				#print "Discarding empty line in fontspec"
		#				continue
		#			parameter = itemlist[0]
		#			value = itemlist[1]
		#			if parameter[0] == "#":
		#				# This is a comment line
		#				continue
		#			elif parameter in self.fonttypes:
		#				self.fontlist[parameter] = value
		#			elif parameter == "musicfontsize":
		#				self.musicfontsize = value
		#				#print "Setting music font size", value
		#except:
		#	pass
		for font in self.fonttypes:
			self.fontnames.append(self.fontlist[font])
		#print self.fontlist
		#print self.fontnames
	def make_fontstring(self,fontname):
		"""Function to generate rtf string to select a particular font
		designated by name"""
		fontindex = self.fonttypes.index(fontname)
		return "\\f" + str(fontindex) + " "
	def get_key_string(self, clef, key):
		#print clef, key
		key = int(key)
		if clef=="alto" or clef == "C" or clef=="C3":
			sharp_notes = ['e','b','f','c']
			flat_notes = ['A','d','G','c']	
		elif clef=="bass" or clef == "F":
			sharp_notes = ['d','A','e','b']
			flat_notes = ['G','c','F','b']	
		elif clef == "C1":
			sharp_notes = ['A','e','b','f','c']
			flat_notes = ['d','g','c','f', 'b']		
		elif clef == "C2":
			sharp_notes = ['c','G','d','A','E']
			flat_notes = ['f','b','e','A', 'd']		
		elif clef == "C4":
			sharp_notes = ['G','d','A','e','b']
			flat_notes = ['c','f','b','e', 'A']	
		elif clef == "C5":
			sharp_notes = ['b','f','c','g','d']
			flat_notes = ['e','A','d','G', 'c']	
		else:
			sharp_notes = ['f','c','g','d']
			flat_notes = ['b','e','A','d']

		keystring = ""
		if key>0:
			# A key with sharps
			keystring += self.make_fontstring("sharpsfont")
			if key>4:
				logging.fatal("Key with too many sharps")
				exit()
			for i in range (0, key):
				keystring += sharp_notes[i]
		elif key <0:
			# Flat key
			keystring += self.make_fontstring("flatsfont")
			key = abs(key)
			if key>4:
				logging.fatal("Key with too many flats")
				exit()
			for i in range (0, key):
				keystring += flat_notes[i]
		logging.debug ("keystring is" + keystring)
		return keystring
	def make_direct(self,next_note, voice):
		#print next_note, voice.name, voice.get_note_position(next_note)
		#exit()
		note_position = voice.get_note_position(next_note)
		try:
			symbol = self.char_table[note_position]
		except:
			symbol = "+"
		return self.make_fontstring("directfont") + symbol		
	def get_meter(self, meter):
		meter  = int(meter)
		if meter == 2: return 'Q'
		elif meter == 3: return 'w'
		elif meter == 6: return 'w'
		elif meter == 9: return 'w'
		elif meter == 12: return 'w'
		elif meter == 16: return 'q'
		elif meter == 24: return 'w'
		elif meter == 4: return 'q'
		else: return '+'
	def get_clef(self, symbol, line, octave):
		# Return the correct clef symbol to be printed in rtf file
		clef = symbol
		if symbol == "C" and not line == 3:
			#This is a 'movable' C clef
			clef = symbol+str(line)
		if ((symbol == "G") or (symbol=="treble")) and (int(octave) == -1):
			clef = "treble-8"
		#print symbol,line,octave,clef,self.clefsymbols[clef]
		try:
			return self.clefsymbols[clef]
		except:
			return "+"

class tunedata:
	title = "Default title"
	composer = ""
	bars_per_line = 6
	voicelist = {}
	voice_sequence = []		# To sort voices into right order
	maxbars = 12
	maxchars = 25
	newlinemode = "bars"
	single_accidentals = False

class voicedata:
	"""
	Within each tune, voices are represented by the voicedata class.
	
	A voicedata object is created dynamically, every time a new 
	voice is encountered. 	"""	
	sharps = [3,0,4,1,5,2,6]
	flats = [6,2,5,1,4,0]
	octaves = [0,1,2,3,4,5,6,7]
	def __init__(self, tune_object):
		self.id = ""
		self.name = ' '
		self.key=0
		self.mode = ""
		self.clef= ""		
		self.clef_octave = 0
		self.middle = 0			
		self.clef_line=0
		#self.note_offset=0		
		self.m1 =0				
		self.m2 = 0
		self.new_key = 0
		self.new_mode = ""
		self.new_clef= ""		
		self.new_clef_octave = 0
		self.new_middle = 0			
		self.new_clef_line=0
		#self.new_note_offset=0		
		self.new_m1 =0				
		self.new_m2 = 0
		self.semibreve_length =256
		self.barcount = 0
		self.maxbars = tune_object.maxbars
		self.charcount = 0
		self.maxchars = tune_object.maxchars
		self.newlinemode = tune_object.newlinemode
		self.single_accidentals = tune_object.single_accidentals
		self.keysig_sharpflats = [0] *100	 # List of sharps/flats by virtue of key signature
		self.lyric_line = ""
		self.lyric_word = ""
		self.all_lyrics = ""
		self.length = self.semibreve_length/4
		self.tie = False			# Flag used for processing tied notes
		self.last_note = 0			# Flag used for accidentals
		self.last_accidental = 0
		self.events = []			# list of events in this voice
		self.pitch = []			# List of note names (if the event is a note)
		self.lengths = []		# List of lengths corresponding to the notes (if event is note)
		self.accidentals = []	# List of accidentals. Sharp +1, flat -1, none 0, natural 8
		self.others = []			# List of other parameters associated with events
    						# NB each event should populate all lists, possibly
    						# with null entries
    						
	def append_event(self,event,note,length,accid,other):
		"""
		Adds an event to the event list. Events are such things as notes, rests clefs, etc"""
		#Check if we're starting a new music line and add clef and key sig if necessary
		#if (not event == "lyricline") and (len(self.events)>0) and (self.events[-1] == "newline"):
		#	self.events.append("start_noteline")
		#	self.pitch.append(0)
		#	self.lengths.append(0)
		#	self.accidentals.append(0)
		#	self.others.append(0)
		countable_events = ["note"] #, "rest"]
		self.events.append(event)
		self.pitch.append(note)
		self.lengths.append(length)
		self.accidentals.append(accid)
		self.others.append(other)
		if event in countable_events:
			self.charcount += 1
		if self.charcount >= self.maxchars:
				self.charcount = 0
				self.do_line_end("chars")
	def extend_last_note (self, duration):
		"""This method deals with tied notes. When called, it adds an additional duration 
		(passed as a parameter) to the last event of type 'note'"""
		for i, e in reversed(list(enumerate(self.events))):
			if e == "note":
				self.lengths[i] += duration
				break
	def check_bars(self):
		self.barcount +=1
		if self.barcount >= self.maxbars:
			self.barcount = 0
			self.do_line_end("bars")
	def do_line_end(self, type):
		if not type == self.newlinemode:
			return
		self.append_event("newline", 0,0,0,0)	
		if self.lyric_line:
			self.append_event("lyricline", 0, 0, 0, self.lyric_line)
			self.all_lyrics +=self.lyric_line + "\\line "
			self.lyric_line = ""	
		self.append_event("start_noteline", 0,0,0,0)
	def get_note_position(self, note):
		"""Convert a note to a position on the staff. Notes are numbered sequentially from C1. 
		Positions are from 2 ledger lines below the staff"""
		position = note-self.middle+8
		return position
	def add_syllable(self,syllabic_type, text):
		if syllabic_type == "single":
			self.lyric_line += " "+text
		elif syllabic_type == "begin":
			self.lyric_word = text
		elif syllabic_type == "middle":
			self.lyric_word += text
		elif syllabic_type == "end":
			self.lyric_word += text
			self.lyric_line += " " + self.lyric_word
	def check_accidental(self, pitch, accidental):	
		#print pitch, accidental, self.keysig_sharpflats[pitch]
		#print self.keysig_sharpflats
		if self.single_accidentals:
			if self.last_note == pitch and self.last_accidental == accidental:
				return 0
		self.last_note = pitch
		self.last_accidental = accidental
		if accidental > self.keysig_sharpflats[pitch]:
			return 1
		elif accidental < self.keysig_sharpflats[pitch]:
			return -1
		return 0
	def set_keysig(self, fifths, mode):	
		fifths = int(fifths)
		if fifths>4 or fifths<-4:
			logging.fatal("This program only supports key signatures up to 4 sharps or flats")
			exit()
		self.key = fifths
		self.mode = mode
		sharps = [3,0,4,1,5,2,6] # F C G D A E B
		flats = [6,2,5,1,4,0]		# B E A D G C
		octaves = [0,1,2,3,4,5,6,7]
		self.keysig_sharpflats = [0] *100 # Re-initialise table
		if fifths == 0:
			return	# Nothing to do
		elif fifths >0:
			for i in range(fifths):
				s = sharps[i]
				for o in octaves:
					self.keysig_sharpflats[s + o*7] = 1
		else:
			fifths= -fifths
			for i in range(fifths):
				f = flats[i]
				for o in octaves:
					self.keysig_sharpflats[f + o*7] = -1	
							

