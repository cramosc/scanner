import argparse
import xml.etree.ElementTree as ET

import os
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
            response = requests.get(base_url + '/Scan/Jobs/' + job_id + '/Pages/1')
            return response.content
        except Exception as error:
            print(repr(error))
            pass


def scan_and_get_content(base_url):
    scan(base_url)
    time.sleep(1)
    last_job_id = get_last_job_id(base_url)
    return get_page(base_url, last_job_id)


def get_file_path():
    current_dir = os.getcwd()
    print('Filename:')
    filename = sys.stdin.readline()
    return os.path.join(current_dir, filename)


def main():
    parser = argparse.ArgumentParser(description='Scan documents')
    parser.add_argument(
        '--ip',
        help='ip address of HP printer',
        required=False,
        default=IP
    )
    options = parser.parse_args()
    base_url = f'http://{options.ip}'

    print('Are you ready to scan a document?')
    print('To start press enter')
    sys.stdin.readline()

    pdf_merger = PdfFileMerger()

    another_page = True
    while another_page:
        try:
            content = scan_and_get_content(base_url)
            pdf_merger.append(content)
        except Exception as error:
            print('Error:', repr(error))
            print(f'Is the ip {options.ip} correct?')
        else:
            print('Another page? [y]/n')
            another = sys.stdin.readline()
            another_page = another.lower() in ('n', 'no')

    file_path = get_file_path()
    with open(file_path, 'wb') as f:
        pdf_merger.write(f)

    print('Completed')
    print(f'Scanned document written in {file_path}')


if __name__ == '__main__':
    sys.exit(main())