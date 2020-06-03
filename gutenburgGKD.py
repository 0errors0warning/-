# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 14:31:34 2020

@author: MSI-PC
"""

import urllib
import re
import os
import zipfile
import gzip
import datetime
import codecs
import glob
import shutil
import ssl
import requests  # 用于获取网页
from bs4 import BeautifulSoup  # 用于分析网页
import re  # 用于在网页中搜索我们需要的关键字
requests.packages.urllib3.disable_warnings()
headers={
  'user-agent':'Mozilla/5.0'
}
ssl._create_default_https_context = ssl._create_unverified_context
MIRROR = " https://gutenberg.pglaf.org/"
LANGUAGE = "English"

def download(img_link,img_name,rawdata):
    imgname1=img_name
    img_name+=rawdata
    from urllib.request import urlretrieve
    import os  # 这个是用于文件目录操作
    if os.path.exists(imgname1) == False:  # 如果文件不存在，创建文件
        os.mkdir(imgname1)
        urlretrieve(img_link, './'+img_name+'.jpg') #从img_link这个网址获取文件，存储到./img_name.jpg的这个文件路径中去，注意要手动加上后缀
    else:
        urlretrieve(img_link, './'+img_name+'.jpg')
    
def older(a, b):

    if not os.path.exists(a) or not os.path.exists(b):
        return False
    sta = os.stat(a)
    stb = os.stat(b)
    return sta <= stb


def fetch(mirrorurl, filename, outputfilename):

    mustdownload = False
    if os.path.exists(outputfilename):
        st = os.stat(outputfilename)
        modified = datetime.date.fromtimestamp(st.st_mtime)
        today = datetime.date.today()
        if modified == today:
            print ("%s 存在最新版，无需下载." % outputfilename)
        else:
            print ("%s 有较新版，需要下载 " % outputfilename)
            mustdownload = True
    else:
        print ("%s需要下载" % outputfilename)
        mustdownload = True

    if mustdownload:
        url = mirrorurl + filename
        urllib.request.urlretrieve(url, outputfilename)


if not os.path.exists("indexes"):
    os.mkdir("indexes")

if not os.path.exists("ebooks-zipped"):
    os.mkdir("ebooks-zipped")

if not os.path.exists("ebooks-unzipped"):
    os.mkdir("ebooks-unzipped")



fetch(MIRROR, "GUTINDEX.zip", "indexes/GUTINDEX.zip")
if not os.path.exists("indexes/GUTINDEX.ALL") or older("indexes/GUTINDEX.ALL", "indexes/GUTINDEX.zip"):
    zipfile.ZipFile("indexes/GUTINDEX.zip").extractall("indexes/")
else:
    pass



fetch(MIRROR, "ls-lR.gz", "indexes/ls-lR.gz")
if not os.path.exists("indexes/ls-lR") or older("indexes/ls-lR", "indexes/ls-lR.gz"):
    inf = gzip.open("indexes/ls-lR.gz", "rb")
    outf = open("indexes/ls-lR", "wb")
    outf.write(inf.read())
    inf.close()
    outf.close()
else:
    pass
mirrordir = {}
mirrorname = {}
re_txt0file = re.compile(r".*? (\d+\-0\.zip)") 
re_txt8file = re.compile(r".*? (\d+\-8\.zip)") 
re_txtfile = re.compile(r".*? (\d+\.zip)") 
for line in open("indexes/ls-lR"):
    if line.startswith("./"):
        line = line[2:].strip()
        if line.endswith(":"):
            line = line[:-1]
        if line.endswith("old") or "-" in line:
            continue
        lastseendir = line
        continue
    m = re_txt0file.match(line)
    if not m:
        m = re_txt8file.match(line)
    if not m:
        m = re_txtfile.match(line)
    if m:
        filename = m.groups()[0]
        if "-" in filename: 
            nr, _ = filename.split("-")
        elif "." in filename: 
            nr, _ = filename.split(".")
        else:
            pass
        ebookno = int(nr)
        if not ebookno in mirrordir:
            mirrordir[ebookno] = lastseendir
            mirrorname[ebookno] = filename


print ("Parsing book index...")
inpreamble = True
ebooks = {} 
ebookslanguage = {} 
ebookno = None
nr = 0
langre = re.compile(r"\[Language: (\w+)\]")
for line in codecs.open("indexes/GUTINDEX.ALL", encoding="utf8"):
    line = line.replace(u"\xA0", u" ") 

    if inpreamble: 
        if "TITLE and AUTHOR" in line:
            inpreamble = False
        else:
            continue

    if not line.strip():
        continue 

    if line.startswith("<==End of GUTINDEX.ALL"):
        break 

    if line.startswith((u" ", u"\t", u"[")):

        m = langre.search(line)
        if m:
            language = m.group(1)
            ebookslanguage[ebookno] = language
    else:

        parts = line.strip().rsplit(" ", 1)
        if len(parts) < 2:
            continue
        title, ebookno = parts
        title = title.strip()
        try:
            if ebookno.endswith(("B", "C")):
                ebookno = ebookno[:-1]
            ebookno = int(ebookno)

            ebooks[ebookno] = title
        except ValueError:
            continue 

for nr, title in ebooks.items():
    if not nr in ebookslanguage:
        ebookslanguage[nr] = "English"

if 1:

    nr = 0
    for ebookno in sorted(ebooks.keys()):
        if ebookslanguage[ebookno] != LANGUAGE:
            continue
        titel = ebooks[ebookno].encode("ascii", "replace")
        filename = mirrorname.get(ebookno, "UNKNOWN")
        filedir = mirrordir.get(ebookno, "UNKNOWN")
        print ("%d. %s (%s in %s)" % (ebookno, titel, filename, filedir))
        nr += 1
    print ("%d ebooks found for language %s" % (nr, LANGUAGE))

for nr, ebookno in enumerate(sorted(ebooks.keys())):
    if ebookslanguage[ebookno] != LANGUAGE: 
        continue
    filedir = mirrordir.get(ebookno)
    filename = mirrorname.get(ebookno)
    if not filedir or not filename:
        continue
    url = MIRROR + filedir + "/" + filename
    rurl= MIRROR + filedir + "/" +filename[:len(filename)-6:]+'-h/images/'
    fn = os.path.join("ebooks-zipped", filename)
    i_n = os.path.join("eimg", filename)
    if 1:
        html=requests.get(rurl,verify=False)
# (?<=A).*?(?=B) 
        soup = BeautifulSoup(html.text,'html.parser')
        tmplist = soup.find_all('a')
        pattern = re.compile('<a href="(.*?).jpg">')
        for i in range(len(tmplist)):
            tmplist[i]=str(tmplist[i])         
        for i in range(len(tmplist)): 
            rawdata = re.findall(pattern, (tmplist[i]))
            
            if rawdata:
                print(rawdata)
                download(rurl+rawdata[0] +'.jpg','eimg/'+filename+'/' ,rawdata[0])
    if os.path.exists(fn):
        print ("(%d/%d) %s 存在，无需下载" % (nr, len(ebooks), fn))
    else:
        print(fn)
        fff=re.compile(r'ebooks-zipped\\0')
        if not fff.search(fn):
            
          print ("(%d/%d) 下载 %s..." % (nr, len(ebooks), fn))

          print(url)
          try:
              urllib.request.urlretrieve(url, fn)
          except :
              pass
errors = []
for fn in glob.glob("ebooks-zipped/*.zip"):
    print ("解压中", fn)
    try:
        zipfile.ZipFile(fn).extractall("ebooks-unzipped/")
    except zipfile.BadZipfile:
        errors.append("Error: 无法解压 %s" % fn) 

for dirn in glob.glob("ebooks-unzipped/*"):
    if os.path.isdir(dirn):
        print ("moving", dirn)
        for fn in glob.glob(os.path.join(dirn, "*")):
            parts = fn.split(os.sep)
            ofn = os.path.join("ebooks-unzipped", parts[-1])
            if os.path.exists(ofn):
                os.unlink(ofn)
            shutil.move(fn, "ebooks-unzipped")
        os.rmdir(dirn)

if errors:
    print ("Errors:")
    for error in errors:
        print( error)
