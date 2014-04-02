import re
import requests
import grequests
from random import choice
import subprocess
import os
from os.path import isfile
from bs4 import BeautifulSoup


r = requests.get('http://wallbase.cc/toplist')
soup = BeautifulSoup(r.text)

thumbnails = soup(class_="thumbnail")

urls = []

for thumb in thumbnails:
    url = thumb.contents[3]('a')[3]('img')[0]["data-original"]
    pattern = re.compile(r'([\d]+)')
    number = pattern.findall(url)[0]
    url = 'http://wallpapers.wallbase.cc/rozne/wallpaper-{}.jpg'
    if not isfile('wallpaper-{}.jpg'.format(number)) and \
       not isfile('wallpaper-{}.png'.format(number)):
        urls.append(url.format(number))

# Let's get all the images.
rs = (grequests.get(u) for u in urls)
results = grequests.map(rs)
successful = filter(lambda r: r.status_code == 200, results)
failed = filter(lambda r: r.status_code == 404, results)
rest = [x for x in results if x not in (successful + failed)]

# Let's try those pesky 404 urls again but with the right extensions.
urls = map(lambda x: x.url.replace('jpg', 'png'), failed)
rs = (grequests.get(u) for u in urls)
files = (grequests.map(rs) + successful)

for r in files:
    filename = r.url.rsplit('/')[::-1][0]
    with open(filename, 'wb') as f:
        f.write(r.content)

files_regex = r'wallpaper-[0-9]+.(png|jpg)'
filenames = [f for f in os.listdir('.') if re.match(files_regex, f)]
subprocess.call(['feh', '--bg-fill', choice(filenames)])
