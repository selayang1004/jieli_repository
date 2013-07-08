# kwokjieli 20130101
# -*- coding:utf-8 -*-
#code reference = http://docs.python.org/release/2.6.6/
import sys,codecs, unicodedata,re, os,glob,shutil
from lxml import etree
reload(sys)
sys.setdefaultencoding('utf-8')

class sutra_gram_arrange_Class:
	def walk_all_obj(self,dir_path):
		os.path.walk(dir_path,self.read_sample_str,'')
		
	def read_sample_str(self,arg,dirIn,fix_length_sample):
		global n,List_Gram4all
		for sample in fix_length_sample:
			if os.path.isfile(os.path.join(dirIn,sample)):
				n=n+1
				print str(n).zfill(4)+'/1049 '+sample
				fi = codecs.open(os.path.join(dirIn,sample),'r','utf-8')
				for line in fi:
					line=line.strip()
					gram,num = line.split(',')
					if gram not in List_Gram4all:
						List_Gram4all[gram]=int(num)
					else:
						List_Gram4all[gram]=List_Gram4all[gram]+int(num)
				fi.close()
n=0
List_Gram4all={}

Root_Path = r'D:\01 Cloud Computing Usage\Dropbox\001 coding\python\00. coding for project\dynasty(Jing_words_count)'

main_program = sutra_gram_arrange_Class()
main_program.walk_all_obj(Root_Path)

#sortitem=[(value,key) for key,value in List_Gram4all.items()]
#sortitem.sort(reverse=True) list comprihensive

with codecs.open('All_grams(before_sort).txt','w','utf-8') as fo:
	for v in List_Gram4all:
		fo.write("%s,%s \r\n" %(v,List_Gram4all[v]))


