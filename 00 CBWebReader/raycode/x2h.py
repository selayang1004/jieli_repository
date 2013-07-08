# coding: utf8
''' 讀 CBETA P4 XML 轉出 HTML 供 web版 CBReader 使用
'''
import collections, os, re, sys
from string import Template
from lxml import etree
import zbx.xml, zbx.str

FOLDER_IN='xml'
FOLDER_OUT='output/html_punc'
FOLDER_NOPUNC='output/html_nopunc'
FOLDER_TEMP='output/temp'
PUNC_SQL = '../output/punc-sql'

# 內容不輸出的元素
PASS=['back', 'docNumber', 'mulu', 'teiHeader']

# 忽略下一層的 white space
IGNORE=['TEI', 'text']

# empty element
EMPTY = ['lb', 'pb']

chars={}

def buf(s):
	global globals
	globals['html'] += s

def write_file(punc): # boolean input
	html = globals['html']
	if punc:
		html = re.sub('<punc>(.*?)</punc>', r'\1', html)
		folder = os.path.join(FOLDER_OUT, globals['collection'], globals['vol'])
	else:
		html = re.sub('<punc>.*?</punc>', '', html)
		folder = os.path.join(FOLDER_NOPUNC, globals['collection'], globals['vol'])
	if not os.path.exists(folder):
		os.makedirs(folder)
	juan_id = '{}_{}'.format(globals['sutra_no'], globals['juan'])
	print(juan_id)
	fn = os.path.join(folder, juan_id + '.htm')
	fo = open(fn, 'w', encoding='utf8')
	fo.write("<div id='text' data-juan='{}'>".format(juan_id))
	fo.write(html)
	fo.write('</div>')
	fo.close()
	
def write_punc_sql():
	save_punc_pos()
	folder = os.path.join(PUNC_SQL, globals['collection'], globals['vol'])
	if not os.path.exists(folder):
		os.makedirs(folder)
	juan = '{}_{}'.format(globals['sutra_no'], globals['juan'])
	fn = os.path.join(folder, juan + '.sql')
	fo = open(fn, 'w', encoding='utf8')
	for k, v in globals['punc-pos'].items():
		pos = ' '.join(v)
		print("INSERT INTO puncs SET juan='{}', punc='{}', position='{}', uid='%s';".format(juan, k, pos), file=fo)
	fo.close()
	
def write_buf(juan):
	global globals
	if globals['juan'] is None:
		globals['juan'] = juan
		return
	write_file(True)
	write_file(False)
	write_punc_sql()
	globals['html'] = ''
	globals['juan'] = juan

def save_punc_pos():
	punc = globals['punc-buf']
	if punc != '':
		punc = re.sub('　+(<p>|<br/>)', r'\1', punc)
		globals['punc-buf'] = ''
		pos = '{}_{}'.format(globals['lb'], globals['count'])
		if punc in globals['punc-pos']:
			globals['punc-pos'][punc].append(pos)
		else:
			globals['punc-pos'][punc] = [pos]
			
def new_char(c):
	save_punc_pos()
	globals['count'] += 1
	id = 'c{}_{}'.format(globals['lb'], globals['count'])
	return '<char id="{}">{}</char>'.format(id, c)
	
def new_punc(c):
	globals['punc-buf'] += c
	return '<punc>' + c + '</punc>'

class XMLTransformer():
	def __init__(self):
		self.ab_type=[]
		self.div_level=0

	def handleText(self, s):
		if s is None: return ''
		s=s.replace('\n', '')
		s=s.replace('&', '&amp;')
		s=s.replace('<', '&lt;')
		char_pattern=r'(?:\[[^\]]*?\]|&[^;]*?;|[A-Za-z\.\d]+|.)'
		chars=re.findall(char_pattern, s, re.DOTALL)
		r = ''
		for c in chars:
			if c in zbx.str.puncs:
				r += new_punc(c)
			else:
				r += new_char(c)
		buf(r)

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

	def handle_gaiji(self, e):
		r=''
		uni=e.get('uni', '')
		if uni!='':
			if re.match(r'[\dA-F]+$', uni):
				return chr(int(uni, 16))
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
		
	def handle_node(self, e):
		if e.tag==etree.Comment: 
			return ''
		if e.tag in PASS:
			return ''
		r=''
		parent = e.getparent()
		if e.tag=='byline':
			buf(new_punc('<p>'))
			self.traverse(e)
		elif e.tag=='gaiji': 
			c = self.handle_gaiji(e)
			buf(new_char(c))
		elif e.tag=='head':
			buf(new_punc('<p>'))
			self.traverse(e)
		elif e.tag=='juan':
			buf(new_punc('<p>'))
			self.traverse(e)
		elif e.tag=='milestone':
			if e.get('unit') == 'juan':
				write_buf(e.get('n').zfill(3))
		elif e.tag=='l':
			self.traverse(e)
			buf(new_punc('　　'))
		elif e.tag=='lb':
			n = e.get('n')
			if parent.tag == 'lg':
				buf(new_punc('<br/>'))
			globals['lb'] = n
			globals['count'] = 0
			buf('<lb id="lb_{}"/>'.format(n))
		elif e.tag=='lg':
			buf(new_punc('<p>'))
			self.traverse(e)
		elif e.tag=='lem':
			self.traverse(e)
		elif e.tag=='note':
			place = e.get('place')
			if place=='inline':
				buf(new_punc('('))
				self.traverse(e)
				buf(new_punc(')'))
		elif e.tag=='p':
			buf(new_punc('<p>'))
			self.traverse(e)
		elif e.tag=='rdg':
			pass
		elif e.tag=='t':
			place=e.get('place', '')
			if place!='foot':
				self.traverse(e)
		else:
			self.traverse(e)
		return

def parse_xml(source):
	global globals
	tree = etree.parse(source)
	tree = zbx.xml.stripNamespaces(tree)
	xt=XMLTransformer()
	
	#e=tree.find('.//title')
	
	xt.traverse(tree.getroot())
	write_buf('') # ??
	return
	
def handle_ent(fn_in, fn_out):
	with open(fn_in,'r',encoding='cp950') as fi:
		s=fi.read()
		temp=s.replace('<?xml version="1.0" encoding="big5" ?>', '')
		temp=temp.strip()
		if temp=='':
			return False
		s=re.sub('^(<\?xml version="1.0" encoding=")big5', r'\1utf8', s)
	with open(fn_out,'w',encoding='utf8') as fo:
		fo.write(s)
	return True

def xml_big5_to_utf8(fn_in, fn_out, ent_exist):
	with open(fn_in, 'r', encoding='cp950') as fi:
		s=fi.read()
	if not ent_exist:
		s=s.replace('%ENTY;', '')
	s=re.sub('^(<\?xml version="1.0" encoding=")cp950(" \?>)', r'\1utf8\2', s)
	s=re.sub('^(<\?xml version="1.0" encoding=")big5(" \?>)', r'\1utf8\2', s)
	s=s.replace('&unrec;', '<unclear/>')
	s=s.replace('&lac;', '<space quantity="0"/>')
	s=s.replace('&lac-space;','<space quantity="1" unit="chars"/>')
	s=s.replace('\r\n<pb ', '<pb ')
	s=s.replace('CBETA.Maha', 'CBETA.maha')
	s=s.replace('CBETA.cp', 'CBETA.pan')
	s=re.sub(r'<div\d+', r'<div', s)
	s=re.sub(r'</div\d+>', r'</div>', s)
	with open(fn_out, 'w', encoding='utf8') as fo:
		fo.write(s)

def handle_sutra(folder_in, folder_temp, sutra):
	print(sutra)
	global globals
	globals['html'] = ''
	globals['juan'] = None
	globals['punc-pos'] = {}
	globals['punc-buf'] = ''
	
	# 將 ent 檔轉為 utf8, 存到 temp 資料夾
	ent_in=os.path.join(folder_in, sutra+'.ent')
	ent_out=os.path.join(folder_temp, sutra+'.ent')
	ent_exist=handle_ent(ent_in, ent_out)
	
	fn_in=os.path.join(folder_in, sutra+'.xml')
	fn_temp=os.path.join(folder_temp, sutra+'.xml')
	# 將 xml 轉為 utf8, 存到 temp 資料夾
	xml_big5_to_utf8(fn_in, fn_temp, ent_exist)
	parse_xml(fn_temp)

def handle_vol(vol):
	global globals
	globals['collection']=vol[:1]
	globals['vol']=vol
		
	temp=os.path.join(FOLDER_TEMP, vol)
	if not os.path.exists(temp):
		os.makedirs(temp)
		
	source=os.path.join(FOLDER_IN, vol)
	fs=os.listdir(source)
	sutras=[]
	for f in fs:
		if f.endswith('.xml'):
			sutra = f[:-4]
			globals['sutra_no']=sutra
			handle_sutra(source, temp, sutra)
			
# main
globals={}

arg = ''
if len(sys.argv)>1:
	arg=sys.argv[1]
	arg=arg.upper()

vols=os.listdir(FOLDER_IN)
for vol in vols:
	if os.path.isdir(os.path.join(FOLDER_IN, vol)):
		if arg=='' or vol.startswith(arg):
			handle_vol(vol)
			
