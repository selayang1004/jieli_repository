# kwokjieli 20130101
# -*- coding:utf-8 -*-
#code reference = http://docs.python.org/release/2.6.6/
import sys,codecs, unicodedata,re, os,glob,shutil
from lxml import etree
reload(sys)
sys.setdefaultencoding('utf-8')

PUNCS=(' ', '~', '!', '@', '#', '$', '%', '/', '\\', '^', '&', '*', '(', ')', '[', ']', '{', '}', '-', '+', '=', '<', '>', ';', ':', ',', '.', '?', '`','\n', '\r', "'", '"', '　', '，', '。', '！', '．', '；', '：', '︰', '？', '、', '—','「', '」', '『', '』', '《', '》', '（', '）', '【', '】', '〈', '〉', '〔', '〕', '”', '“','─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼','○', '▲', '■', '□', '◇', '…', '●', '◎', '∴', '△', '▽', '◑', '←', '→')

# 內容不輸出的元素
PASS=['back', 'docNumber', 'mulu', 'teiHeader' , 'juan' , 'byline', 'milestone', 't','head','note','rdg']
# juan>mulu>jhead>title, byline, milestone
# rdg 其他本子的斠勘不要

# 果睿：忽略下一層的 white space; 捷立：此tag 下一層的text 全部不要
IGNORE=['TEI.2', 'text'] 

USED = ['l','lb','lg','lem','p','t','gaiji','pb','app','div','body','item','anchor','list','foreign','space','sic','tt','trailer']

# all_tag
ALLTAG = PASS + IGNORE + USED

class UnicodeTransform_Class:
	def handle_ent(self,fn_in, fn_out):
		with codecs.open(fn_in,'r',encoding='cp950') as fi:
			s=fi.read()
			temp=s.replace('<?xml version="1.0" encoding="big5" ?>', '')
			temp=temp.strip()
			if temp=='':
				return False
			s=re.sub('^(<\?xml version="1.0" encoding=")big5', r'\1utf8', s)
		with codecs.open(fn_out,'w',encoding='utf8') as fo:
			fo.write(s)
		return True
	
	def xml_big5_to_utf8(self,fn_in, fn_out, ent_exist):
		with codecs.open(fn_in, 'r', encoding='cp950') as fi:
			s=fi.read()
		if not ent_exist: 
			s=s.replace('%ENTY;', '')
		s=re.sub('^(<\?xml version="1.0" encoding=")cp950(" \?>)', r'\1utf8\2', s)
		s=re.sub('^(<\?xml version="1.0" encoding=")big5(" \?>)', r'\1utf8\2', s)
		# dtd 的位置
		s=re.sub('(<!DOCTYPE TEI.2 SYSTEM ")../dtd/(cbetaxml.dtd")',r'\1%s\2' % DTD_cbeta, s)
		s=re.sub('(<!ENTITY % CBENT SYSTEM ")../dtd/(cbeta.ent">)',r'\1%s\2' % DTD_cbeta,s)
		s=re.sub('(<!ENTITY % JAP SYSTEM ")../dtd/(jap.ent">)',r'\1%s\2' % DTD_cbeta,s)
		
		s=s.replace('&unrec;', '<unclear/>')
		s=s.replace('&lac;', '<space quantity="0"/>')
		s=s.replace('&lac-space;','<space quantity="1" unit="chars"/>')
		s=s.replace('\r\n<pb ', '<pb ')
		s=s.replace('CBETA.Maha', 'CBETA.maha')
		s=s.replace('CBETA.cp', 'CBETA.pan')
		s=re.sub(r'<div\d+', r'<div', s)
		s=re.sub(r'</div\d+>', r'</div>', s)
		with codecs.open(fn_out, 'w',encoding='utf8') as fo:
			fo.write(s)

class cbetaSutraXML_Class:
	def stripNamespaces(self,tree):
		# http://wiki.tei-c.org/index.php/Remove-Namespaces.xsl
		xslt_root = etree.XML('''\
		<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
		<xsl:output method="xml" indent="no"/>

		<xsl:template match="/|comment()|processing-instruction()">
			<xsl:copy>
				<xsl:apply-templates/>
			</xsl:copy>
		</xsl:template>

		<xsl:template match="*">
			<xsl:element name="{local-name()}">
				<xsl:apply-templates select="@*|node()"/>
			</xsl:element>
		</xsl:template>

		<xsl:template match="@*">
			<xsl:attribute name="{local-name()}">
				<xsl:value-of select="."/>
			</xsl:attribute>
		</xsl:template>
		</xsl:stylesheet>
		''')
		transform = etree.XSLT(xslt_root)
		tree = transform(tree)
		return tree
	
	def write_txt_obj(self,s):
		global globals
		globals['html'] += s

	def parseXML_obj(self,src_file):
		#print 'Parse this to txt = ' + os.path.split(src_file)[-1] 
		tree = etree.parse(src_file)
		tree = self.stripNamespaces(tree)
		
		self.traverse(tree.getroot())

	def traverse(self, node):
		if node is None: return ''
		r=''
		tag=node.tag
		if tag not in IGNORE: 
			self.handleText(node.text)
		for n in node.iterchildren(): 
			self.handle_node(n)
			if tag not in IGNORE:
				self.handleText(n.tail)
	
	def handle_node(self, e): # 若此標籤還有下一層就要繼續 traverse
		parent = e.getparent()
		# 可以寫兩行，找出不在ALLTAG，沒處理的 tag
		#if e.tag not in ALLTAG: 
		#	print e.tag
		if e.tag==etree.Comment: # 註解不要 
			return ''
		if e.tag in PASS: # 這以下的元素不要
			return ''
		elif e.tag=='gaiji': # 這個讓它輸出另一個結果，不需要寫入 plain text
			# handle_gaiji(e.tag) #20130624
			return ''
			# c = self.handle_gaiji(e)先不做
		elif e.tag=='l': # 偈頌
			self.traverse(e)
		elif e.tag=='lb':
			self.traverse(e)
		elif e.tag=='lg':
			self.traverse(e)
		elif e.tag=='lem':
			self.traverse(e)
		elif e.tag=='p':
			self.traverse(e)
		elif e.tag=='t': # 悉曇字和漢字對照 term 對照 ，<t resp="CBETA" lang="chi">要的
			if e.get('place'):
				pass
			else:
				self.traverse(e)
		else: # 不需要處理的就繼續走
			self.traverse(e)
		return

	def handle_gaiji(self, e): # 處理缺字和組字式
		r=''
		uni=e.get('uni', '')
		if uni!='':
			if re.match(r'[\dA-F]+$', uni):
				return chr(int(uni, 16)) # 轉成 16進位
			tokens = re.findall('&#x(.*?);', uni)
			for t in tokens:
				if t=='':
					continue
				r+=chr(int(t, 16))
			return r

		cx=e.get('cx', '')
		if cx!='':
			tokens=re.findall('＆(CB04608)；', cx)
			for t in tokens:
				if t.startswith('CB'):
					r+= '[' + t + ']'
				else:
					print('error 96', cx)
					exit(1)
			return r
		ref=e.get('cb')
		return '[' + ref + ']'

	def handleText(self, s):
		if s is None: return ''
		s=s.replace('\n', '') # 變成一行
		s=s.replace('&', '&amp;')
		s=s.replace('<', '&lt;')
		# char_pattern=r'(?:\[[^\]]*?\]|&[^;]*?;|[A-Za-z\.\d]+|.)' # 組字式 | entity | 英文和數字 | 任何字元
		# substring=re.findall(char_pattern, s, re.DOTALL)
		
		for p in PUNCS:
			s = s.replace(p,'')
		self.write_txt_obj(s)
	
class parseCat_Class:
	UT_Class = UnicodeTransform_Class()
	CSX = cbetaSutraXML_Class()
	
	def through_all_dir_obj(self,folderin):
		os.path.walk(os.path.join(folderin,Catalogue_Dir),self.list_all_dir_obj,'')
		os.path.walk(os.path.join(folderin,'dynasty(Jing_in_part)'),self.clean_xml2txt_obj,'')
		os.path.walk(os.path.join(folderin,'dynasty(Jing_Combine)'),self.fixed_length_obj,'')
		os.path.walk(os.path.join(folderin,'dynasty(Jing_Thousandwords)'),self.cut_ngram_obj,'')
		
	def list_all_dir_obj(self,arg,dirIn,fileInside): # 從目錄撈資料
		for i in fileInside: # 檔案名稱是以 list 的資料型態出現
			if i[-13:]=='catalogue.txt':
				self.create_same_dir_obj(os.path.join(dirIn,i))
	
	def cut_ngram_obj(self,arg,dirIn,sample_slice):
		global Times
		for sample_txt in sample_slice:
			if os.path.isfile(os.path.join(dirIn,sample_txt)):
				fo_dir_path = os.path.split(os.path.join(dirIn,sample_txt).replace('dynasty(Jing_Thousandwords)','dynasty(Jing_words_count)'))[0]
				
				fn,ext=os.path.splitext(sample_txt)
				
				fon = os.path.join(fo_dir_path,fn+'_ngram'+ext)
				
				Times = Times +1
				
				print '%04d/%s %s'%(Times,Total_sample,fn+'_ngram'+ext)
				
				with codecs.open(os.path.join(dirIn,sample_txt), 'r',encoding='utf8') as fi:
					s=fi.read()
				
				mydict = {}
				
				for gram in range(Gram_MIN,Gram_MAX):
					for i in range(len(s)-(gram-1)):
						sc = int(i + gram) # sc= start count
						word_count = s[sc-gram:sc]
						if word_count not in mydict:
							mydict[word_count]=s.count(word_count)
							#print 'now is working in %s'%FileName
							
					sortitem=[(value,key) for key,value in mydict.items()]
					sortitem.sort()
					sortitem.reverse()
				
				with codecs.open(fon, 'w',encoding='utf8') as fo:
					for v in sortitem:
						fo.write("%s,%s \r\n" %(v[1],v[0]))
				

	def clean_xml2txt_obj(self,arg,dirIn,sutra_xml):
		global globals
		for list_all in sutra_xml:
			if os.path.isfile(os.path.join(dirIn,list_all)) and list_all[-4:]=='.xml':
				globals['html'] = ''
				self.CSX.parseXML_obj(os.path.join(dirIn,list_all))
				sutra_text=globals['html']
				combine_path = os.path.join(dirIn,list_all).replace('dynasty(Jing_in_part)','dynasty(Jing_Combine)').replace('.xml','.txt')
				with codecs.open(combine_path, 'w',encoding='utf8') as fo:
					fo.write(sutra_text)
	
	def fixed_length_obj(self,arg,dirIn,all_txt):
		global Total_sample
		for combine_txt in all_txt:
			if os.path.isfile(os.path.join(dirIn,combine_txt)):
				fl_dir_path = os.path.split(os.path.join(dirIn,combine_txt).replace('dynasty(Jing_Combine)','dynasty(Jing_Thousandwords)'))[0]
				
				#print os.path.split(os.path.join(dirIn,combine_txt).replace('dynasty(Jing_Combine)','dynasty(Jing_Thousandwords)'))[-1]
				
				fn,ext=os.path.splitext(combine_txt)
				
				with codecs.open(os.path.join(dirIn,combine_txt),'r',encoding='utf8') as fi:
					s=fi.read()
				sutra_length = len(s)
				loops = sutra_length/LENTGH_SAMPLE
				
				if loops==0: # 小於 smaple size 的話，要特別處理
					Total_sample = Total_sample + 1
					fon=os.path.join(fl_dir_path,'%s_%03d_%04d%s'%(fn,0,len(s),ext))
					with codecs.open(fon, 'w',encoding='utf8') as fo:
						fo.write(s)
					
				for sl in range(loops):
					Total_sample = Total_sample + 1
					if sl==(loops-1):
						sample_string=s[sl*LENTGH_SAMPLE:]
						sample_size=sutra_length-sl*LENTGH_SAMPLE
					else:
						sample_string=s[sl*LENTGH_SAMPLE:(sl+1)*LENTGH_SAMPLE]
						sample_size = LENTGH_SAMPLE
					
					fon=os.path.join(fl_dir_path,'%s_%03d_%04d%s'%(fn,sl,sample_size,ext))
					with codecs.open(fon, 'w',encoding='utf8') as fo:
						fo.write(sample_string)
	
	def create_same_dir_obj(self,catalogues_file_path):
		# python3.3 os.makedirs(path, mode=0o777, exist_ok=False) 可以輕易解決
		all_dirs=['dynasty(Jing_in_part)','dynasty(Jing_Combine)','dynasty(Jing_Thousandwords)','dynasty(Jing_words_count)','dynasty(GramafterFilter)'] # 需要存下過程資料的資料夾
		for diff_dir in all_dirs:
			if not os.path.exists(os.path.join(Root_Path,diff_dir)):
				os.mkdir(os.path.join(Root_Path,diff_dir))
			self.copy_tree_obj(os.path.join(Root_Path,Catalogue_Dir),os.path.join(Root_Path,diff_dir))
		fin = codecs.open(catalogues_file_path,'r','utf-8')
		for line in fin:# 每行都是一個需要處理的『經』
			ce_num,jing_num= str(line.strip()).split(',')
			
			cat_path = os.path.split(catalogues_file_path)[0] # 目錄所在的資料夾
			for diff_dir in all_dirs:
				if cat_path.count('dynasty') !=1: # 檢查路徑是否有問題
					print "Careful with the path!!"
					break
				if not os.path.exists(os.path.join((os.path.abspath(cat_path)).replace(Catalogue_Dir,diff_dir),jing_num)):# 在每個譯者下建立屬於他翻譯的經
					#print os.path.join((os.path.abspath(cat_path)).replace(Catalogue_Dir,diff_dir),jing_num)
					os.mkdir(os.path.join((os.path.abspath(cat_path)).replace(Catalogue_Dir,diff_dir),jing_num))
				
			file_name = ce_num+'n'+jing_num[1:] #建立一個檔名，給ent和xml用
			
			ent_src = os.path.join(Source_Path,os.path.join(ce_num,file_name+'.ent'))
			
			ent_dst = os.path.join(os.path.join(os.path.abspath(cat_path),jing_num).replace('dynasty','dynasty(Jing_in_part)'),file_name+'.ent')

			ent_exist=self.UT_Class.handle_ent(ent_src,ent_dst)

			jing_src = os.path.join(Source_Path,os.path.join(ce_num,file_name+'.xml'))
			jing_dst = os.path.join(os.path.join(os.path.abspath(cat_path),jing_num).replace('dynasty','dynasty(Jing_in_part)'),file_name+'.xml')

			self.UT_Class.xml_big5_to_utf8(jing_src, jing_dst, ent_exist)
		
	def copy_tree_obj(self, src, dst): # 複製樹狀資料夾
		files = os.listdir(src)
		for f in files:
			path = os.path.join(src, f)
			if os.path.isdir(path):
				dst_path = os.path.join(dst, f)
				if not os.path.exists(dst_path):
					os.mkdir(dst_path)
				else:
					self.copy_tree_obj(path, dst_path)
	
class sutra_gram_arrange_Class:
	def walk_all_obj(self,dir_path):
		os.path.walk(dir_path,self.read_sample_str,'')
		self.write_gram_obj(True)
		
	def read_sample_str(self,arg,dirIn,fix_length_sample):
		global gram_count,List_Gram4all
		for sample in fix_length_sample:
			if os.path.isfile(os.path.join(dirIn,sample)):
				gram_count=gram_count+1
				print str(gram_count).zfill(4)+'/1049 '+sample
				fi = codecs.open(os.path.join(dirIn,sample),'r','utf-8')
				for line in fi:
					line=line.strip()
					gram,num = line.split(',')
					if gram not in List_Gram4all:
						List_Gram4all[gram]=int(num)
					else:
						List_Gram4all[gram]=List_Gram4all[gram]+int(num)
				fi.close()

	def write_gram_obj(self,combineneed):
		if combineneed:
			with codecs.open(gram_file_name,'w','utf-8') as fo:
				for v in List_Gram4all:
					fo.write("%s,%s \r\n" %(v,List_Gram4all[v]))
	
# 主程式開始
globals = {}
Times= 0
Total_sample = 0

gram_count=0
List_Gram4all={}

gram_file_name='All_grams(before_sort).txt'# same with sort_gram.py 

# 路徑
DTD_cbeta= r'C:/dtd/' # 要非常注意這個路徑
# DTD_cbeta= '.' # 這樣不行
Root_Path = r'D:\01 Cloud Computing Usage\Dropbox\001 coding\python\00. coding for project' # 輸出資料夾
# under Root_Path, there are 'dynasty(Jing_in_part)','dynasty(Jing_Combine)','dynasty(Jing_Thousandwords)','dynasty(Jing_words_count)','dynasty(GramafterFilter)'
Source_Path = r'D:\01 Cloud Computing Usage\Dropbox\003 work file\CBETA XML coding\xml' # XML 來源檔
Catalogue_Dir='dynasty'

LENTGH_SAMPLE = 2000

Gram_MIN = 2
Gram_MAX = 11

pC =parseCat_Class()
pC.through_all_dir_obj(Root_Path)

sg=sutra_gram_arrange_Class()
sg.walk_all_obj(os.path.join(Root_Path,'dynasty(Jing_words_count)'))


