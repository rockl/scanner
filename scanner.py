#! /usr/bin/python
# -*- coding:utf-8 -*-
import random
import queue
import argparse
import hashlib
import sqlite3
import threading
import time
import os  
from urllib.parse import urlparse
from aiohttp import ClientSession
from requests_html import HTMLSession

blacklist=['pdf']

def get_hyperlink(url):
    session = HTMLSession()
    r = session.get(url)
    hyperlink=r.html.absolute_links
    return hyperlink

def request_fingerprint(url):
    md5_obj = hashlib.md5()
    md5_obj.update(url.encode(encoding='utf-8'))
    md5_url = md5_obj.hexdigest()
    return md5_url

def sqlite_md5(url):
    md5=request_fingerprint(url)
    conn = sqlite3.connect('test.db')
    c = conn.cursor()    
    cmd='''create table IF NOT EXISTS  hash_url(id INTEGER PRIMARY KEY AUTOINCREMENT,hash_value char(32) not null UNIQUE)'''
    c.execute(cmd)
    cmd='''select id from hash_url where hash_value = "%s"'''%(str(md5))
    c.execute(cmd)
    row = c.fetchone()
    #print(row)
    if row == None:
        
        try:
            cmd = '''insert into hash_url (hash_value) values("%s")'''%(str(md5))
            #print("scan url "+url)
            c.execute(cmd)
            q.put(url)
        except (ValueError, sqlite3.OperationalError):
            print("error")
    conn.commit()
    conn.close()

def scan(i,q,lock,host):
    while True:
        lock.acquire()
        if q.qsize()==0:
            print("no element")
            lock.release()
            break
        url=q.get() 
        print("scan url "+url)
        hyperlink= get_hyperlink(url)
        for url in hyperlink:
            print(url)
            if host != urlparse(url).netloc:
                pass
            else:
                sqlite_md5(url)                
        lock.release()
        time.sleep(1)

def threads(thread_num,queue,lock,host):
    threads = []
    for i in range(0,thread_num):
        thread=threading.Thread(target=scan, args=(i,queue,lock,host))
        thread.start()
        threads.append(thread)
    for t in threads: 
        t.join()
    print("exit")

if __name__ == '__main__':
    banner ='''
                    _    _ 
                   | |  | |
     _ __  __   ___| | _| |
    | '__/ _ \ / __| |/ / |
    | | | (_) | (__|   <| |
    |_|  \___/ \___|_|\_\_|
    '''
    print(banner)
    parser = argparse.ArgumentParser(description="This script uses the aiohttp library's head() method to determine the status word.")
    parser.add_argument("website", type=str, help="The website that needs to be scanned")
    parser.add_argument('-o', '--output', dest="scanOutput", help="Results saved files", type=str, default=0)
    parser.add_argument('-t', '--thread', dest="coroutineNum", help="Number of coroutine running the program", type=int, default=50)
    args = parser.parse_args()
    ########init queue and thread lock#################
    os.system('rm -rf test.db')
    q = queue.Queue()
    lock = threading.Lock()
    host=urlparse(args.website).netloc
    print("spider host :%s",host)
    hyperlink=get_hyperlink(args.website)
    ##############init queue###########################
    for url in hyperlink:
        print(url)
        if host != urlparse(url).netloc:
            pass
        else:
            sqlite_md5(url)
            
    #########start threads#############################
    threads(args.coroutineNum,q,lock,host)
    print("* End of scan.")
