#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
'''
Get charts on BGP prefixes and peers for a given AS-number. Data is based on
Hurricane Electric's BGP toolkit.
'''

# Core modules
from __future__ import print_function
from argparse import ArgumentParser
from urllib2 import urlopen, quote, Request, HTTPError
from datetime import datetime
from shutil import copyfile
from os import makedirs, path, strerror
import json
import re
import sys


# Third-party modules
from bs4 import BeautifulSoup
import argcomplete

# Metadata
__author__ = 'Tor Inge Skaar'
__license__ = "LGPL"
__version__ = "1"

# Configuration
URL = 'http://bgp.he.net/'
UA = 'Mozilla/5.0 (X11; ; Linux i686; rv:1.9.2.20) Gecko/20110805'
CACHE = '/tmp/bgpchart'
VERBOSE = False


def in_cache(cachefile):
    '''Check if we have a valid cache for the given data. Return True/False.'''

    # Create cache dir if it doesn't exist
    try:
        makedirs(CACHE)
        return False
    except OSError as e:
        if not path.isdir(CACHE):
            exit('Failed to create cache directory: {}'.format(str(e)))

    if not path.isfile(cachefile):
        # No cached data
        return False

    now = datetime.now().strftime('%d')
    lastupd = datetime.fromtimestamp(path.getmtime(cachefile)).strftime('%d')

    if now > lastupd:
        # Cached data is too old
        return False

    return True


def fetchdata(url):
    '''Retrieve data from the URL provided'''

    # Set the UA, and try to fetch the page
    req = Request(url, headers={'User-Agent': UA})
    try:
        data = urlopen(req).read()
    except HTTPError as e:
        exit('Failed to retrieve {} (Error: {})'.format(url, e.code))
    return data


def parsedata(page, asn):
    '''Parse the given HTML page for chart data for given ASN'''

    # Safe characters for quoting
    safechars = "%/:=&?~#+!$,;'@()*[]"

    soup = BeautifulSoup(page)
    asinfo = soup.find('div', {'id': 'asinfo'})
    data = {}
    for img in asinfo.findAll('img'):
        if img['alt'].startswith('AS' + asn):
            data[img['alt']] = quote(img['src'], safechars)
    return data


def savefile(data, filepath):
    '''Save the given data to the given filepath'''

    try:
        if isinstance(data, dict):
            data = json.dumps(data)
        f = open(filepath, 'w+')
        f.write(data)
        f.close()
    except IOError as e:
        exit('Failed to write to: {} ({})'.format(filepath, strerror(e.errno)))


def readfile(filepath):
    '''Read the given filepath and return contents'''

    try:
        with open(filepath, "r") as f:
            data = f.read()
    except IOError as e:
        exit('Failed to read: {} ({})'.format(filepath, strerror(e.errno)))
    if filepath.endswith('.json'):
        data = json.loads(data)
    return data


def debug(msg):
    '''Output debug message to console if verbose flag is set'''

    if VERBOSE:
        print('[DEBUG] {}'.format(msg), file=sys.stderr)


def main(input):
    '''Main execution'''

    desc = 'Charts for BGP prefixes and peers'
    parser = ArgumentParser(description=desc)
    parser.add_argument('asn', help='AS-number to lookup')
    parser.add_argument('-ip', choices=['v4', 'v6'], default='v4',
                        help='IP version 4 (default) or 6 statistics')
    parser.add_argument('-c', choices=['a', 'o', 'p'], default='a',
                        help='Chart type: prefixes [a]nnounced (default) or '
                        '[o]riginated, or [p]eer count')
    parser.add_argument('-o', metavar='path',
                        help='Output directory where charts are saved')
    parser.add_argument('-v', action='store_true',
                        help='Verbose console output (debugging)')
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.v
    debug('Verbose flag is set')

    # Validate ASN
    m = re.match('^(AS)?(\d{1,10}$)', args.asn, re.IGNORECASE)
    if m is None:
        exit('Invalid AS-number')
    asn = m.group(2)
    ASURL = URL + 'AS' + asn
    debug('ASURL: {}'.format(ASURL))

    # Which chart does the user want
    chart = 'AS' + asn + ' IP' + args.ip + ' '
    if args.c == 'a':
        chart += 'Prefixes Announced Chart'
    elif args.c == 'o':
        chart += 'Prefixes Originated Chart'
    else:
        chart += 'Peer Count Chart'
    debug('Chart selection ({}): {}'.format(args.c, chart))

    # Do local caching. HE provides a free service, lets not abuse it.
    datafile = CACHE + '/AS' + asn + '.json'
    chartfile = CACHE + '/AS' + asn + '-' + args.ip + '-' + args.c + '.png'
    chartimg = ''
    validchart = False
    validdata = False
    if in_cache(chartfile):
        # Valid cached chart
        validchart = True
        debug('Valid chart cache: {}'.format(chartfile))
    else:
        debug('Cache miss: {}'.format(chartfile))
        if in_cache(datafile):
            # No chart, but we have valid data cache
            validdata = True
            srclinks = readfile(datafile)
            debug('Valid data cache: {}'.format(datafile))
        else:
            # Complete cache miss
            debug('Cache miss: {}'.format(datafile))
            page = fetchdata(ASURL)
            debug('Fetched: {}'.format(ASURL))
            srclinks = parsedata(page, asn)
            debug('Parsed: AS{} -> Got {} links'.format(asn, len(srclinks)))

        chartimg = fetchdata(srclinks[chart])
        debug('Fetched: {}'.format(srclinks[chart]))
        if not validdata:
            savefile(srclinks, datafile)
            debug('Cached: {}'.format(datafile))
        if not validchart:
            savefile(chartimg, chartfile)
            debug('Cached: {}'.format(chartfile))

    if args.o is None:
        outfile = path.basename(chartfile)
        debug('No output defined - Using default')
    else:
        outfile = args.o
    debug('Output file: {}'.format(outfile))

    # Output chart
    try:
        copyfile(chartfile, outfile)
        print('Saved {}: {}'.format(chart, outfile))
    except IOError as e:
        exit('Failed to copy file from cache: {} ({}) to {}'
             .format(chartfile, strerror(e.errno)), outfile)


if __name__ == '__main__':
    main(sys.argv)
