#! /usr/bin/python

import sys
import os
from os.path import isfile, join, isdir
import re
from optparse import OptionParser
from random import choice
import subprocess

from bs4 import BeautifulSoup
import requests
import grequests


parser = OptionParser()
parser.add_option('-c', '--clean', action='store_true', default=False,
                  dest='clean', help='Remove cached wallpapers')
parser.add_option('-s', '--sketchy', action='store_true', default=False,
                  dest='sketchy',
                  help='Include "sketchy" wallpapers (maybe NSWF)')
parser.add_option('-o', '--output-dir', dest='output_dir', default='/tmp/',
                  help='directory in which wallpapers should be stored')


def get_purity(include_sketchy):
    if include_sketchy:
        return '110'
    else:
        return '100'


def get_new_wallpapers(options):
    urls = []
    purity = get_purity(options.sketchy)
    r = requests.get('http://wallbase.cc/toplist?purity=%s' % purity)
    soup = BeautifulSoup(r.text)

    thumbnails = soup(class_="thumbnail")
    for thumb in thumbnails:
        url = thumb.contents[3]('a')[3]('img')[0]["data-original"]
        match = re.match(r'.*-(\d+)\.(jpg|png)', url)
        if not match:
            sys.stderr.write("Unable to construct url from thumbnail: " % url)
            continue
        number, ext = match.groups()
        url = 'http://wallpapers.wallbase.cc/rozne/wallpaper-%s.%s'
        filename = join(options.output_dir, 'wallpaper-%s.%s' % (number, ext))
        if not isfile(filename):
            urls.append(url % (number, ext))
    return urls


def download_wallpapers(urls, output_dir):
    rs = map(grequests.get, urls)
    results = grequests.map(rs)
    files = filter(lambda r: r.status_code == 200, results)

    for r in files:
        filename = r.url.rsplit('/')[-1]
        with open(join(output_dir, filename), 'wb') as f:
            f.write(r.content)


def set_random_wallpaper(output_dir):
    files_regex = r'wallpaper-\d+.(png|jpg)'
    filenames = [join(output_dir, f)
                 for f in os.listdir(output_dir)
                 if re.match(files_regex, f)]
    subprocess.call(['feh', '--bg-fill', choice(filenames)])


def main(options):
    output_dir = options.output_dir
    urls = get_new_wallpapers(options)

    # Let's get all the images.
    download_wallpapers(urls, output_dir)

    set_random_wallpaper(output_dir)


def clean_temporary_files(options):
    output_dir = options.output_dir
    files = [f for f in os.listdir(output_dir) if f.startswith('wallpaper-')]
    for f in files:
        os.remove(join(output_dir, f))


if __name__ == '__main__':
    options, args = parser.parse_args()
    if not isdir(options.output_dir):
        sys.stderr.write('%s is not a directory\n' % options.output_dir)
        sys.exit(1)
    if options.clean:
        clean_temporary_files(options)
    else:
        main(options)
