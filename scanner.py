#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET

import os
import subprocess

import requests
import sys
from PyPDF2 import PdfFileMerger

import time

IP = '192.168.0.208'


def scan(base_url):
    print('Scanning...')
    requests.post(base_url + '/Scan/Jobs', data="""
        <scan:ScanJob xmlns:scan="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/">
        <scan:XResolution>300</scan:XResolution>
        <scan:YResolution>300</scan:YResolution>
        <scan:XStart>0</scan:XStart>
        <scan:YStart>0</scan:YStart>
        <scan:Width>2480</scan:Width>
        <scan:Height>3508</scan:Height>
        <scan:Format>Pdf</scan:Format>
        <scan:CompressionQFactor>25</scan:CompressionQFactor>
        <scan:ColorSpace>Color</scan:ColorSpace>
        <scan:BitDepth>8</scan:BitDepth>
        <scan:InputSource>Platen</scan:InputSource>
        <scan:GrayRendering>NTSC</scan:GrayRendering>
        <scan:ToneMap>    
            <scan:Gamma>1000</scan:Gamma>
            <scan:Brightness>1000</scan:Brightness>
            <scan:Contrast>1000</scan:Contrast>
            <scan:Highlite>179</scan:Highlite>
            <scan:Shadow>25</scan:Shadow>
        </scan:ToneMap>
        <scan:ContentType>Document</scan:ContentType>
        </scan:ScanJob>
    """)


def get_last_job_id(base_url):
    response = requests.get(base_url + '/Jobs/JobList')
    xml = ET.fromstring(response.text)
    url = xml[-1].find('{http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30}JobUrl').text
    return url.split('/')[-1]


def get_page(base_url, job_id):
    while True:
        try:
            time.sleep(2)
            print('Scanning...')
            url = base_url + '/Scan/Jobs/' + job_id + '/Pages/1'
            response = requests.get(url)
            return response.content
        except Exception as error:
            print(repr(error))


def scan_and_get_content(base_url):
    scan(base_url)
    time.sleep(1)
    last_job_id = get_last_job_id(base_url)
    return get_page(base_url, last_job_id)


def get_file_path():
    current_dir = os.getcwd()
    print('Filename:')
    filename = sys.stdin.readline().strip('\n')
    filename = filename or 'scanned_document'
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    return os.path.join(current_dir, filename)


def create_temp_file(content, page_number):
    temp_file = os.path.join(os.getcwd(), '__scanned__document__{}__'.format(page_number))
    temp_file_broken = temp_file + 'broken'
    with open(temp_file_broken, 'wb') as f:
        f.write(content)

    try:
        subprocess.check_output(['qpdf', temp_file_broken, temp_file], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        pass

    os.remove(temp_file_broken)
    return temp_file


def main():
    parser = argparse.ArgumentParser(description='Scan documents')
    parser.add_argument(
        '--ip',
        help='ip address of HP printer',
        required=False,
        default=IP
    )
    options = parser.parse_args()
    base_url = 'http://{}'.format(options.ip)

    print('Are you ready to scan a document?')
    print('To start press enter')
    sys.stdin.readline()

    pdf_merger = PdfFileMerger()

    another_page = True
    page_number = 1
    temp_files = []
    while another_page:
        try:
            content = scan_and_get_content(base_url)
            temp_file = create_temp_file(content, page_number)

            pdf_merger.append(temp_file)
            temp_files.append(temp_file)
        except Exception as error:
            print('Error:', repr(error))
            print('Is the ip {} correct?'.format(options.ip))
            return 1
        else:
            print('Another page? [y]/n')
            another = sys.stdin.readline().strip('\n')
            another_page = another.lower() not in ('n', 'no')
            page_number += 1

    file_path = get_file_path()
    with open(file_path, 'wb') as f:
        pdf_merger.write(f)

    for temp in temp_files:
        os.remove(temp)

    print('Completed')
    print('Scanned document written in {}'.format(file_path))


if __name__ == '__main__':
    sys.exit(main())