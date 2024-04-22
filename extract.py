import argparse
import json
import time
import chardet
import requests
from bs4 import BeautifulSoup, Comment, CData
from trafilatura import extract
from urllib.parse import urlparse

publisher_domain = 'www.atpress.ne.jp'
company_keywords = ["株式会社","有限会社","合同会社" ,"合名会社" ,"合資会社","社団法人","財団法人","協会"]

def contains_domain(url, domain):
    parsed_url = urlparse(url)
    url_domain = parsed_url.netloc.lower()
    return domain.lower() in url_domain

def custom_error(code):
    outputs = {
                "meta": {
                    "code": code
                }
            }
    response = json.dumps(outputs, ensure_ascii=False, indent=4)
    print(response)
    return response

def extractURL(url):
    #cuong-san: create list check source host name
    LIST_CHECK_SOURCE_HOSTNAME = [
        {'hostname': "excite.co.jp", 'tag_name': 'a', 'tag_value': 'id', 'value': 'logo'},
        {'hostname': "mapion.co.jp", 'tag_name': 'a', 'tag_value': 'href', 'value': 'http://www.mapion.co.jp/'},
    ]
    #cuong-san: Change User-Agent
    headers={
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", 
      'Accept': '*/*',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        outputs = {
                "meta": {
                    "code": response.status_code
                }
            }
        response = json.dumps(outputs, ensure_ascii=False, indent=4)
        print(response)
        return response

    encoding = chardet.detect(response.content)['encoding']

    if encoding != "MacRoman":
        try:
            html = response.content.decode(encoding)
        except Exception as e:
            html = response.content.decode(response.encoding, 'ignore')
    else:
        html = response.content.decode(response.encoding, 'ignore')

    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(["ol", "ul", "dl", "aside", "iframe"]):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "author"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "writerbox"}):
        tag.decompose()
    for tag in soup.find_all("section", {"id": "writer-profile"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "c-ttl-article-author"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "post-author"}):
        tag.decompose()
    # special case
    for tag in soup.find_all("div", {"class": "relevants"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "share"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "more-link-normal"}):
        tag.decompose()
    for tag in soup.find_all("div", {"class": "more-link-alt"}):
        tag.decompose()

    #check ratio 
    # Get text content
    
    # Get the remaining HTML content

    html_content = str(soup)
    text = soup.get_text()
    text_length = len(text.strip())
    
    # Get total HTML content length
    html_length = len(response.text)
    # print(text_length)

    # print(html_length)

    
    ##############
    html = str(soup)
    # print(html)

    extract_result = extract(html, output_format='json',
                             url=url, include_images=False)
    extract_data = json.loads(extract_result)
    ## Get ratio
    leng_content = len(extract_data["text"])
    # print(len(extract_data["text"]))

    ratio_content_text = len(extract_data["text"]) / html_length
    ratio_soup_text = text_length / html_length

    # print(ratio_content_text)
    if (((ratio_content_text < 0.008) and (leng_content < 1000)) and (ratio_soup_text < 0.01 or html_length <50000)): 
        # print("IS_NOT_DETAIL_PAGE")
        outputs = {
                "meta": {
                    "code": 203, 
                    "message" : "IS_NOT_DETAIL_PAGE"
                }
            }
        response = json.dumps(outputs, ensure_ascii=False, indent=4)
        return response
    ## cuong-san:  Check source hostname  
    check_exist_source={}
    source_hostname=''
    for i, d in enumerate(LIST_CHECK_SOURCE_HOSTNAME):
        if d['hostname'] == extract_data["hostname"]:
            check_exist_source = LIST_CHECK_SOURCE_HOSTNAME[i]
    if check_exist_source: 
        for tag in soup.find_all(check_exist_source['tag_name'], {check_exist_source['tag_value']: check_exist_source['value']}):
            img_tag = tag.find('img')
            if img_tag:
                source_hostname = img_tag['alt']
    if len(extract_data["text"]) < 50:
        return custom_error(404)
    
    pubs_elements = soup.find_all(class_="pubs")

    publisher = None
    if pubs_elements:
        for pubs_element in pubs_elements:
            publisher_elements = pubs_element.find_all(class_="publisher")
            if publisher_elements:
                for publisher_element in publisher_elements:
                    publisher = publisher_element.text.strip()
                    break
            if publisher is not None:
                break

    if contains_domain(url, publisher_domain):
        author = None
        if publisher is not None:
            for keyword in company_keywords:
                publisher = publisher.replace(keyword, "")
            publisher.replace("\n", "")
            publisher.strip()
            author = publisher
    else:
        author = extract_data["author"]
    ## cuong-san:  Set new source_hostname if existed
    if check_exist_source: 
        extract_data["source-hostname"] = source_hostname
    outputs = {
                "data": {
                    "title": extract_data["title"],
                    "description": extract_data["excerpt"],
                    "contents": extract_data["text"],
                    "author": author,
                    "hostname": extract_data["hostname"],
                    "date": extract_data["date"],
                    "categories": extract_data["categories"],
                    "tags": extract_data["tags"],
                    "fingerprint": extract_data["fingerprint"],
                    "id": extract_data["id"],
                    "license": extract_data["license"],
                    "comments": extract_data["comments"],
                    "language": extract_data["language"],
                    "pagetype": extract_data["pagetype"],
                    "source": extract_data["source"],
                    "source-hostname": extract_data["source-hostname"],
                    "excerpt": extract_data["excerpt"],
                    "url": url,
                    "created_at": int(time.time() * 1000),
                    "imagePath": [],
                    "startend": {}
                },
                "meta": {
                    "code": 200
                }
            }
    response = json.dumps(outputs, ensure_ascii=False, indent=4)
    print(response)
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, help='URL', required=True)

    args = parser.parse_args()
    try:
        extractURL(args.url)
    except:
        custom_error(500)