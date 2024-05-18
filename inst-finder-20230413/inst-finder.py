#!/usr/bin/python3
#
# Institute Finder (inst-finder) Ver.2023-04-13
# Naohiko Otsuka (IAEA Nuclear Data Section)
#
from time import sleep
import difflib
import os
import pyperclip
import re
import sys
import unicodedata

# Removal of acccent symbols
def normalize_unicode(words: str) -> str:
  unicode_words = ""
  for character in unicodedata.normalize("NFD", words):
    if unicodedata.category(character) != "Mn":
      unicode_words += character
  return unicode_words

# Extraction of institute dictionary
def create_instdict():
  f=open(dict_file, 'r')
  lines=f.readlines()
  f.close()
  for line in lines:
    code=line[0:7]
    exp=line[11:66]
    if line[71:74] == "003" and line[11:12]=="(" and line[79:80] != "O":
      exp=re.search('^\((.+)\)', exp)
      exp=exp.group(1)
      dic_inst[code]=exp       # dic_inst['3ZZZIAE']=IAEA
      if code[1:4]==code[4:7]:
        dic_coun[exp]=code     # dic_coun[Japan]=2JPNJPN

# Creation of additional array for international institutions
def create_zzzcdict():
  if os.path.exists("./dict_zzzc.txt"):
    f=open('dict_zzzc.txt', 'r')
  else:
    print ("Error: Input file dict_zzzc.txt is missing.")
    exit()

  lines=f.readlines()
  f.close()
  for line in lines:
    line=line.rstrip("\x0D?\x0A?")
    code=line[0:7]
    coun=line[8:12]
    exp=line[13:]
    exp=re.sub("^\s+|\s+$", '', exp)
    dic_zzzc[code]=coun        # dic_zzzc['3ZZZIAE']=2AUS
    dic_zzze[code]=exp         # dic_zzze['3ZZZIAE']=International Atommic Energy Agency

# Creation of country abbreviation dictionary
def create_cnabdict():
  if os.path.exists("./dict_cnab.txt"):
    f=open('dict_cnab.txt', 'r')
  else:
    print ("Error: Input file dict_cnab.txt is missing.")
    exit()

  lines=f.readlines()
  f.close()
  for line in lines:
    line=line.rstrip("\x0D?\x0A?")
    abb=line[0:32]
    cnt=line[33:]
    abb=re.sub("^\s+|\s+$", '', abb)
    cnt=re.sub("^\s+|\s+$", '', cnt)
    dic_cnab[abb]=cnt         # dic_cnab['UK']=United Kingdom

# Creation of a list of prefices of phrases to be omitted
def create_prefdict():
  if os.path.exists("./dict_pref.txt"):
    f=open('dict_pref.txt', 'r')
  else:
    print ("Error: Input file dict_pref.txt is missing.")
    exit()

  lines=f.readlines()
  f.close()
  for line in lines:
    line=line.rstrip("\x0D?\x0A?")
    dic_pref.append(line)

# Creation of a list of alias
def create_aliadict():
  if os.path.exists("./dict_alia.txt"):
    f=open('dict_alia.txt', 'r')
  else:
    print ("Error: Input file dict_alia.txt is missing.")
    exit()

  lines=f.readlines()
  f.close()
  for line in lines:
    line=line.rstrip("\x0D?\x0A?")
    phrase=line[0:54]
    phrase=phrase.rstrip()
    alias=line[55:]
    if alias==".":
      alias=""
    dic_alia[phrase]=alias

# Creation of code list for the country and its distance with the text
def dist_text_code(line,country):
  code=dic_coun[country]
  code_coun=code[0:4]
  dic_inst_part=({key:value for key, value in dic_inst.items() if code_coun in key})

  for code in dic_zzzc: # addition of international organizations to the array for the country
    if dic_zzzc[code]==code_coun:
      dic_inst_part[code]=dic_zzze[code]

  for code in dic_inst_part: # calculation of distance between two texts
    dist=difflib.SequenceMatcher(None,line,dic_inst[code]).ratio()
    dist="{:.3f}".format(dist)
    dists[code]=dist

# Selection of the correct institute code
def code_selection(dists_arr,country,line,auto):
  i=0
  id=9999
  code=[]
  code.append("")
  l=len(dists_arr)
  for dist_tup in dists_arr:
    i+=1
    char=str(i)
    char="{:>3s}".format(char)
    code.append(dist_tup[0])
    print ("   ["+char+"] "+dist_tup[0]+"("+dist_tup[1]+") "+dic_inst[dist_tup[0]])
    if char=="  1":
      print ("")
    if i%5==0 or i==l:
      print ("   [  0] "+dic_coun[country]+"("+dists[dic_coun[country]]+") "+country)
      while id==9999:
        if auto==1:
          char="1"
        else:
          char=input("\n   Hit return to see more candidates. Type 0 to choose the country code -> ")
          print ()
        if re.compile("\d+").search(char):
          id=int(char)
          if id<0 or id>i:
            id=9999
          continue
        elif char=="":
          break
      if char=="":
        print ("++ "+line+"\n")
      elif id>0 and id<=i:
        print ("   Your choice: "+code[id]+"="+dic_inst[code[id]]+"\n")
        return code[id]
      elif id==0:
        print ("   Your choice: "+dic_coun[country]+"="+country+"\n")
        return dic_coun[country]
  print ("   ... OK. We assign the country code: "+dic_coun[country]+"\n")
  return dic_coun[country]

# Removal or replacement of some words
def clean_text(line):
  line=line.rstrip()
  line=normalize_unicode(line)

# e.g., Istituto Nazionale di Fisica Nucleare -> INFN
  for alias in dic_alia:
    if re.compile('^({})'.format(alias)).search(line):
      line=re.sub(alias, dic_alia[alias], line)

  phrases=line.split(",")
  country=phrases[-1]
  country=country.lstrip()
  text=""
  for phrase in phrases:
    phrase=re.sub("^\s+|\s+$", '', phrase)
    char=""

# e.g., Faculty of Science, Kyoto University, Japan -> Kyoto University, Japan
    for pref in dic_pref:
      if re.compile('^({})'.format(pref)).search(phrase):
        phrase=""
    if phrase!="":
      text=text+", "+phrase
  text=re.sub("^, ", "", text)
  return (text,country)

# final printing
def print_inst(outputs_file,outputs_exfo):
  f=open('inst-finder.log', 'a')
  for line in outputs_file.keys():
    char=entry+" "+outputs_file[line]+" "+line+"\n"
    f.write(char)
  f.close()

  print("INSTITUTE  (",end="")
  i=0
  l=len(outputs_exfo.keys())
  code_coun=[]
  for code in outputs_exfo.keys():
    if code[1:4]==code[4:7]:
      code_coun.append(code)
      l-=1
    else:
      i+=1
      if (i%6==1 and i!=1):
        print (",\n            ",end="")
      elif i!=1:
        print (",", end="")
      print(code,end="")
      if i==l:
        break
  print (")")
  for code in code_coun:
    print ("           ("+code+")")

# get text from website by copy 
def get_webtext():
  print ("Copy institute text from web page (Ctrl+c when complete):\n")
  char_old=pyperclip.paste()
  webtext=""
  try:
    while True:
      if pyperclip.paste()!=char_old:
        char=pyperclip.paste() 
        webtext=webtext+"\n"+char
        char_old=char
        print(char)
        sleep(0.5) 
  except KeyboardInterrupt:
    print ("\nInput completed\n")
    return (webtext)

# print text with formatting
def print_text(text,length,offset1,offset2):
  words=text.split()
  words.append("XXX")
  char="";
  nl=1
  for word in words:
    if len(char+" "+word)<length and word!="XXX":
      char=char+" "+word
    else:
      if nl==1:
        offset=offset1
      else:
        offset=offset2
      for i in range(offset-1):
        print (" ",end="")
      print (char)
      nl+=1
      char=" "+word
  print()

print ("------------------------------------------------------------------")
print ("             INST-FINDER: EXFOR Institute Code Finder")
print ("------------------------------------------------------------------")

auto=0
#auto=1
dic_inst=dict()
dic_coun=dict()
dic_zzzc=dict()
dic_zzze=dict()
dic_cnab=dict()
dic_alia=dict()
dic_pref=[]
outputs_file=dict()
outputs_exfo=dict()

args=sys.argv
if len(args)==2:
  dict_file=args[1]
  if not os.path.exists(dict_file):
    print ("Error: Dictionary file "+dict_file+" is missing.")
    exit()
else:
  print ("Error: Specify the TRANS dictionary file name.")
  print ("       (e.g., 'python3 inst-finder.py trans.9127').")
  exit()
  
entry=""
while not re.compile("^\w\d{4,4}$").search(entry):
  entry=input("Type entry number.\n")
  if not re.compile("^\w\d{4,4}$").search(entry):
    print ("This entry number is invalid!\n")

create_instdict()
create_zzzcdict()
create_cnabdict()
create_prefdict()
create_aliadict()

webtext=get_webtext()
lines=webtext.split("\n")
for line in lines:
  line=line.rstrip("\x0D?\x0A?")
  if len(line)<5:
    continue
  elif not "," in line:
    continue
  line=re.sub("^\d+", '',line)
  line=re.sub("^\s+|\s+$", '', line)
  print ("\n++ "+line+"\n")
  var=clean_text(line)
  text=var[0]
  coun_pub=var[1]

  if coun_pub in dic_coun:
    country=coun_pub
  elif coun_pub in dic_cnab:
    country=dic_cnab[coun_pub]
  else:
    char=input("If this is an institute, type its country name, otherwise hit the entre key.\n")
    if char=="":
      continue
    elif char in dic_coun:
      country=char
    elif char in dic_cnab:
      country=dic_cnab[char]
    else:
      print("Unknown country name. We assign 5XXXXXX to this institute.")
      country="5XXXXXX"

  if country=="5XXXXXX":
    code="5XXXXXX"
  else:
    text=re.sub(",\s*"+coun_pub, '', text)
    dists=dict()
    dist_text_code(text,country)
    dists_arr=sorted(dists.items(), key=lambda x:x[1],reverse=True)
    code=code_selection(dists_arr,country,line,auto)

  outputs_file[line]=code
  outputs_exfo[code]=1

print ("---------------------Summary of your selections---------------------")
print ()
for line in outputs_file.keys():
  print (outputs_file[line], end="")
  print_text(line,55,4,11)
print ("--------------------------------------------------------------------")
print ()

while id!="y" and id !="n":
  id=input("Are these correct? (y/n) ")

if (id=="y"):
  print ()
  print_inst(outputs_file,outputs_exfo)

print ()
print ("Good bye!")
exit()
