import re
import json
import os
import codecs

from utils import fatalError, ensureParentDirs

defaultVars = {
    "rootdir": "",
    "title-class": "",
    "timestamp": ""
}

templateTagParser = re.compile( r'(.*){{#include\s*(.*?)#}}(.*)' )
templateTagStartParser = re.compile( r'(.*){{#include\s*(.*?):(.*)' )
templateTagEndParser = re.compile( r'(.*)#}}(.*)' )

varParser = re.compile( r'(.*){{\$(.+?)}}(.*)' )

forTagStartParser = re.compile( r'(.*?){{%for\s+(.*?)\s+in\s+(.*?):(.*)' )
forTagEndParser = re.compile( r'(.*?)%}}(.*)' )

unknownTemplateParser = re.compile( r'{{' )

def ensureDirs( dir ):
    if not os.path.exists(dir):
    	os.makedirs(dir)
def ensureParentDirs( dir ):
	ensureDirs(os.path.dirname(dir))


def loadTemplate( baseName ):
    with codecs.open ( "_templates/" + baseName + ".template.html", "r", "utf-8" ) as f:
        return f.readlines()

def write( filename, generator ):
    ensureParentDirs(filename)
    with codecs.open( filename, "w", "utf-8" ) as outFile:
        for line in generator:
            outFile.write(line)

class Templater:
	def __init__( self, template, vars = defaultVars ):
		self.vars = vars.copy()
		self.template = template

	def applyVar( self, line ):
		replaced = None
		m = varParser.match(line)
		if m:
			name = m.group(2)
			if name in self.vars:
				replaced = m.group(1) + self.vars[name] + m.group(3)
				l = self.applyVar( m.group(1) + self.vars[name] + m.group(3) )
			else:
				print( "** unresolved var: " + name + "**" )
				replaced = m.group(1) + m.group(3)
		if replaced:
			replaced2 = self.applyVar( replaced )
			if replaced2:
				return replaced2
			else:
				return replaced
		return None

	def apply( self, templateLines ):
		templateName = None
		defLines = None
		forVar = None
		forContainer = None

		for line in templateLines:
			if templateName != None:
				m = templateTagEndParser.match(line)
				if m:
					if m.group(1) != '':
						defLines.append( m.group(1) )

					child = Templater( "", self.vars )
					child.vars.update( json.loads( "".join(defLines) ) ) 
					for line in child.apply( loadTemplate(templateName) ):
						yield line
					defLines = None
					templateName = None
					continue
				else:
					defLines.append( line )
				continue
			if forVar:
				m = forTagEndParser.match(line)
				if m:
					if m.group(1).strip() != '':
						defLines.append( m.group(1) )
					if not forContainer in self.vars:
						forVar = None
						continue				
					container = self.vars[forContainer]
					if not hasattr(container, "__len__"):
						fatalError( "** " + forContainer + " is not a container **" )
						forVar = None
						continue
					vars = [var.strip() for var in forVar.split(",")]
					for item in container:
						child = Templater( "", self.vars )

						if len(vars) == 1:
							child.vars[forVar] = item
						else:
							for i, var in enumerate(vars):
								child.vars[var] = item[i]
						for forLine in child.apply( defLines ):
							yield forLine
					forVar = None
					defLines = None
				else:
					defLines.append( line )
				continue

			# single line template
			m = templateTagParser.match(line)
			if m:
				for line in self.apply( loadTemplate(m.group(2)) ):
					yield line
				continue
			
			# multi line template
			m = templateTagStartParser.match(line)
			if m:
				templateName = m.group(2)
				if m.group(3) != '':
					defLines = [m.group(3)]
				else:
					defLines = []
				continue

			# for
			m = forTagStartParser.match(line)
			if m:
				forVar = m.group(2)
				forContainer = m.group(3)
				defLines = []
				continue

			# vars
			replaced = self.applyVar( line )
			if replaced:
				yield replaced + "\n"
				continue

			if unknownTemplateParser.match(line):
				print( "Unknown template in line:\n" + line )

			yield line.rstrip() + "\n"

	def generateContent( self ):
		# Can't rely on Python 3.3, so no `yield from`
		for line in self.apply( loadTemplate( self.template ) ):
			yield line

	def generate( self ):
		yield '<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">'
		for line in self.generateContent():
			yield line
		yield '</html>'

	def writeFile( self, toHtmlFile ):
		print( "Generating: " + toHtmlFile )
		write( toHtmlFile, self.generate() )

