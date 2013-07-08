# coding: utf8
import sys,codecs
fi = codecs.open('All_grams(before_sort).txt', 'r', encoding='utf8')
r = []
count = 0
for line in fi:
	line = line.rstrip()
	(term, i) = line.split(',')
	s = i.zfill(6) + ',' + term
	r.append(s)
	count += 1
	if (count % 100000) == 0:
		print('{:,}'.format(count))
fi.close()

count = 0
fo = codecs.open('All_grams(after_sort).txt', 'w', encoding='utf8')
for s in sorted(r, reverse=True):
	fo.write(s+'\r\n')
	#print(s, file=fo)
	count += 1
	if (count % 100000) == 0:
		print('{:,}'.format(count))
fo.close()