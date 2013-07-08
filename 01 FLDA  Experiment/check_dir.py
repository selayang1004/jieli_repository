# check whether there is txt under T directory or not
# jieli 20130122
# -*- coding:utf-8 -*-
#code reference = http://docs.python.org/release/2.6.6/
import sys,codecs, unicodedata,re, os,glob,shutil
from lxml import etree
reload(sys)
sys.setdefaultencoding('utf-8')

class DoubleCheck_Class:
	def through_check_dir_file_obj(self,folderin):
		for dir in NeedCheckDir:
			os.path.walk(os.path.join(folderin,dir),self.run_all_obj,'')

	def run_all_obj(self,arg,dirIn,fileInside):
		if (os.path.split(dirIn)[-1])[0] =='T' and len(os.listdir(dirIn))==[]:
			#print os.path.split(dirIn)[-1]
			
			print dirIn.split(os.sep)[-4]+' in '+dirIn.split(os.sep)[-1]
			

NeedCheckDir=['dynasty(Jing_in_part)','dynasty(Jing_Combine)','dynasty(Jing_Thousandwords)','dynasty(Jing_words_count)']

Root_Path = r'D:\01 Cloud Computing Usage\Dropbox\001 coding\python\00. coding for project'

Catalogue_Dir='dynasty'

pC =DoubleCheck_Class()
pC.through_check_dir_file_obj(Root_Path)
