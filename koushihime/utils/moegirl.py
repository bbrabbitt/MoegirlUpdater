# -*- coding: utf-8 -*-
"""
Moegirl SDK (api.php/webpage mixed)
"""
import re
import os
import json
from hashlib import md5
from collections import OrderedDict
from datetime import datetime, timedelta
from urllib import urlencode
from urllib2 import Request, urlopen
from bs4 import BeautifulSoup
from flask import current_app
from . import _decode_dict
from koushihime.main.models import BanList


class MoegirlQuery(object):
    """
    An innocent query (JSON).
    
    @attrib title:unicode constructor(title)
    @attrib api_url
    @attrib params:dict   Query params
    @attrib response      Response.
    """
    def __init__(self, title):
        """
        @param title:unicode 标题
        """ 
        self.title = title
        self.api_url = current_app.config["MOEGIRL_API_ROOT"]
        self.params = {'format': 'json', 'action': 'query',
                       'prop': 'categories', 'titles': title}
        self.response = None

    def request(self, **attach_param):
        """
        Executes a urllib2 Request with **attach_param
        attached to self.params
        
        @side_effect sets self.response to response dict
        @side_effect updates self.params with attach_param
        @return self.response:dict
        """
        if attach_param:
            self.params.update(attach_param)
        encode_params = urlencode(self.params)
        request = Request(url=self.api_url, data=encode_params)
        response_object = urlopen(request)
        json_response = response_object.read()
        self.response = json.loads(json_response, object_hook=_decode_dict)
        return self.response

    def get_categories(self):
        """
        Extracts categories for the requested page.
        
        @side_effect self.request, iff response is not present
        @return categories:list<str>
        """
        categories = []
        response = self.response if self.response else self.request()
        if isinstance(response, dict):
            key = response['query']['pages'].keys()[0]
            value = response['query']['pages'][key]
            try:
                for i in range(len(value['categories'])):
                    categories.append(value['categories'][i]['title'])
            except:
                pass
        return categories

    def banned_moegirl_category(self):
        """
        Checks if the requested page is blocked from koushihime pushes.

        @side_effect self.request, iff response is not present
        @return bool
        """
        cat = self.get_categories()
        banned = u"Category:屏蔽更新姬推送的条目".encode('utf-8')
        for i in range(len(cat)):
            if cat[i] == banned:
                return True
        return False

    def get_namespace(self):
        """
        Gets the namespace of the requested title.
        
        @side_effect self.request, iff response is not present
        @return int?
        """
        response = self.response if self.response else self.request()
        response_odict = OrderedDict(response)
        if response['query']['pages'].keys()[0] is not '-1':
            key = response_odict['query']['pages'].keys()[0]
            namespace = response_odict['query']['pages'][key]['ns']
            return namespace
        return None

    def ban_from_regex(self):
        """
        Checks if the requested page is blocked in the local regex BanList.
        
        @return      bool
        @side_effect decrements count for the rule_object hit
        """
        regex_list = BanList.query.all()
        if regex_list:
            for rule_object in regex_list:
                rule = rule_object.rule
                if 'Category:' not in rule:
                    if re.search(rule, self.title.decode("utf-8")):
                        if rule_object.status.count == 0:
                            return True
                        else:
                            self.fresh_rule_push_count(rule_object)
                else:
                    categories = self.get_categories()
                    for category in categories:
                        if re.search(rule[len("Category"):].split(' ')[-1], category):
                            if rule_object.status.count == 0:
                                return True
                            else:
                                self.fresh_rule_push_count(rule_object)
        return False

    @staticmethod
    def fresh_rule_push_count(rule_object):
        rule_object.status.count -= 1
        rule_object.save()


class MoegirlImage(object):
    """
    A questionable image.
    
    @attrib path_root:str  path root
    @attrib url:str        url
    @attrib raw_bytes:str  temp bytes, *str used as raw bytes*, only during init
    @attrib raw_bytes:func reads the saved bytes
    @attrib hash:str       MD5 hash hexdigest
    @attrib path:str       saved path
    @attrib type:str       extension name from URL.
    """
    def __init__(self, title):
        """
        Fills up all attribs from the given title. Includes image-saving.
        
        @param title:(str|unicode)
        """
        self.path_root = "./koushihime/imgcache"
        try:
            self.url = "https://zh.moegirl.org/" + title.encode('utf-8')
        except:
            self.url = "https://zh.moegirl.org/" + title
        self.touch_cache_folder()
        self.raw_bytes = self.get_image()
        self.hash = self.image_hash()
        self.path = self.save_image()
        self.raw_bytes = lambda: open(self.path, 'rb') if self.path else None

    def image_hash(self):
        """
        Returns a MD5 hash if we have the bytes.
        
        @return str
        """
        if self.raw_bytes:
            return md5(self.raw_bytes).hexdigest()
        return ''

    def get_image(self):
        """
        Extracts img.src from a page.

        FIXME: the current dimension-based method is strange.
        div.fullImageLink#file > a['href'] should be used instead.
        
        @side_effect sets self.type.
        @return str:image bytes if successful else None.
        """
        file_page = urlopen(self.url)
        raw_html = file_page.read()
        ssrc = BeautifulSoup(raw_html, "html.parser")
        image_url = None
        try:
            image_div = ssrc.find_all('a', class_='image')
            for image in image_div:
                imgtag = image.find('img')
                if (int(imgtag['width']) > 200 and int(imgtag['height']) > 100):
                    image_url = imgtag['src']
                    break
        except:
            return None
        if image_url:
            self.type = image_url.split('.')[-1]
            try:
                headers = self.cloudflare_headers
                request = Request(url=image_url, headers=headers)
                image = urlopen(request)
                image_bytes = image.read()
            except:
                return None
        else:
            return None
        return image_bytes

    def save_image(self):
        """
        Saves the image to a {path_root}/{hash}.{type}.
        
        @return file_path:str if successful else None.
        """
        if self.raw_bytes and self.hash:
            try:
                file_path = "{0}/{1}.{2}".format(self.path_root, self.hash, self.type)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(self.raw_bytes)
                        f.flush()
                return file_path
            except:
                return None
        return None

    def touch_cache_folder(self):
        """
        Creates self.path_root if it does not exist yet.
        Forget about what `touch` actually is.
        
        @return None
        """
        is_exists = os.path.exists(self.path_root)
        if not is_exists:
            os.makedirs(self.path_root)

    @property
    def cloudflare_headers(self):
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.8,zh-TW;q=0.6,en;q=0.4",
            "cache-control": "max-age=0",
            "cookie": "__cfduid=dfc6b63939d0f061541f2368f5233734b1461485677",
            "if-none-match": "56a5edcc-8cb9",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36"
        }


def get_recent_changes():
    """
    Get recent changes.
    
    @return list of 'recent changes' objects.
    """
    apiurl = "https://zh.moegirl.org/api.php"
    date_format = "%Y%m%d%H%M%S"
    utc = datetime.utcnow()
    rcstart = (utc - timedelta(hours=1)).strftime(date_format)
    rcend = utc.strftime(date_format)
    parmas = urlencode({'format': 'json', 'action': 'query', 'list': 'recentchanges', 'rcstart': rcstart, 'rcend': rcend,
                               'rcdir': 'newer', 'rcnamespace': '0', 'rctoponly': '', 'rctype': 'edit|new', 'continue': '',
                               'rcprop': 'title|sizes'})
    req = Request(url=apiurl, data=parmas)
    res_data = urlopen(req)
    ori = res_data.read()
    change_query = json.loads(ori, object_hook=_decode_dict)
    change_list = change_query['query']['recentchanges']
    return change_list
