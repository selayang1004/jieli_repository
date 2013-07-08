# coding: utf8
''' Convert CBETA P5a XML to Simple XML
讀 CBETA P5a XML 轉出簡易版 XML, 只留下 lb 跟校勘標記

使用範例:
	執行單冊: p5a2sx.py -v t01
	只執行大正藏: p5a2sx.py -c t
	只執行卍續藏: p5a2sx.py -c x
	執行大正藏, 從 T03 開始: p5a2sx.py -c t -s t01

環境: python 3.3
周邦信 2013.2.22
'''
import os, re, sys
from optparse import OptionParser
from lxml import etree
import zbx.xml

FOLDER_IN = 'D:/cbetatmp/cbetap5-3'
FOLDER_OUT='../output/simple-xml'

# 內容不輸出的元素
PASS=['back', 'docNumber', 'mulu', 'teiHeader']

# 忽略下一層的 white space
IGNORE=['TEI', 'text']

# empty element
EMPTY = ['lb', 'pb']

def handle_g(e):
	cb = e.get('ref')[1:]
	if cb.startswith('CB'):
		pua=int(cb[2:])+0xF0000
	elif cb.startswith('SD'):
		pua=int(cb[3:],16)+0xFA000
	elif cb.startswith('RJ'):
		pua=int(cb[3:],16)+0x100000
	return chr(pua)

def handle_text(s):
	if s is None: return ''
	s=s.replace('&', '&amp;')
	s=s.replace('<', '&lt;')
	return s

def traverse(node):
	''' 處理某一個 node 下的所有子節點, 包括 text '''
	if node is None: return ''
	r=''
	tag=node.tag
	if tag not in IGNORE:
		r += handle_text(node.text)
	for n in node.iterchildren(): 
		r += handle_node(n)
		if tag not in IGNORE:
			r += handle_text(n.tail)
	return r

def open_tag(e):
	''' 傳入某一個 element, 傳回 open tag 字串, 包含屬性 '''
	r = '<' + e.tag
	for k, v in e.attrib.items():
		r += ' {}="{}"'.format(k, v)
	if e.tag == 'lb':
		r += '/'
	r += '>'
	return r

def handle_node(e):
	''' 處理一個 node '''
	if e.tag==etree.Comment: # xml comment 內容不要
		return ''
		
	if e.tag in PASS:
		return ''
	r=''
	parent = e.getparent()
	if e.tag in ('app', 'choice', 'corr', 'lb', 'lem', 'rdg', 'sic'): # 要保留標記
		r = open_tag(e)
		r += traverse(e)
		if e.tag != 'lb':
			r += '</{}>'.format(e.tag)
	elif e.tag=='g':
		r = handle_g(e)
	elif e.tag=='l':
		r = traverse(e) + '　　'
	elif e.tag=='note':
		place = e.get('place')
		if place=='inline':
			r = '(' + traverse(e) + ')'
	elif e.tag=='t':
		place=e.get('place', '')
		if place!='foot':
			r = traverse(e)
	else:
		r = traverse(e)
	return r

def handle_sutra(folder_in, sutra):
	''' 處理某一經 '''
	print(sutra)
	
	fn_in=os.path.join(folder_in, sutra+'.xml')
	tree = etree.parse(fn_in)
	tree = zbx.xml.stripNamespaces(tree)
	
	root = tree.getroot()
	r = traverse(root)
	if r.startswith('\n'):
		r = r[1:]
	r = r.replace('\n\n', '\n')
	
	folder = os.path.join(FOLDER_OUT, globals['collection'], globals['vol'])
	os.makedirs(folder, exist_ok=True)
	fn_out = os.path.join(folder, sutra+'.xml')
	fo = open(fn_out, 'w', encoding='utf8')
	fo.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	fo.write('<root>')
	fo.write(r)
	fo.write('</root>')
	fo.close()

def handle_vol(vol):
	''' 處理某一冊 '''
	global globals
	col = vol[:1]
	globals['collection'] = col
	globals['vol'] = vol
		
	source=os.path.join(FOLDER_IN, col, vol)
	fs=os.listdir(source)
	sutras=[]
	for f in fs:
		if f.endswith('.xml'):
			sutra = f[:-4]
			handle_sutra(source, sutra)

def handle_collection(col):
	''' 處理某部藏經, 例如全部大正藏或全部卍續藏 '''
	path = os.path.join(FOLDER_IN, col)
	vols = os.listdir(path)
	for vol in vols:
		if options.vol_start is not None:
			if vol < options.vol_start:
				continue
		handle_vol(vol)

def handle_args():
	''' 取得命令列參數 '''
	parser = OptionParser()
	parser.add_option('-c', dest='collection', help='collections (e.g. TXJ...)')
	parser.add_option('-s', dest='vol_start', help='start volumn (e.g. x55)')
	parser.add_option('-v', dest='vol', help='volumn (e.g. x55)')
	(options, args) = parser.parse_args()

	if options.collection is not None:
		options.collection = options.collection.upper()
		
	if options.vol_start is not None:
		options.vol_start = options.vol_start.upper()
		
	if options.vol is not None:
		options.vol = options.vol.upper()
		
	return (options, args)

# main
globals = {}
(options, args) = handle_args()

if options.vol is not None: # 如果有指定 -v 參數
	handle_vol(options.vol)
elif options.collection is not None: # 如果有指定 -c 參數
	handle_collection(options.collection)