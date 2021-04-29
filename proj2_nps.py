#################################
##### Name: Yasin Shafi
##### Uniqname: yasins
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets as secret # file that contains your API key
import time

BASE_URL = 'https://www.nps.gov/index.htm'
CACHE_FILE_NAME = 'cacheNPS_Scrape.json'
CACHE_DICT = {}

def load_cache():
    '''
    Opens a cache file if it exists. Reads the file, and loads the content as json to a Cache Dictionary and returns it.
    If the file doesn't exist returns an empty Cache Dictionary.
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    '''
    Writes a cache file. Takes a json from the given cache dictionary an writes it to a file.
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    '''
    Checks if the url exists as a key in the cache dictionary. If it does, returns the value of that key.
    If it does not, uses requests to get the data for the url and saves it to the cache dictionary as a value of the url.
    The url is the key. Returns the value of the key.
    '''
    if (url in cache.keys()): 
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_DICT = load_cache()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, url, category= "No Category", name= "No Name", address= "No address", zipcode= "No zipcode", phone= "No phone"):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
        self.url = url # Example of a URL = 'https://www.nps.gov/isro/index.htm'
        url_text = make_url_request_using_cache(self.url, CACHE_DICT)
        # response = requests.get(self.url) #Without Caching

        soup = BeautifulSoup(url_text, 'html.parser') #With Cache
        park_page = soup.find('div', class_="Hero-titleContainer clearfix")
        self.name = park_page.find('a').string
        self.category = park_page.find('span', class_="Hero-designation").string
        park_city = soup.find('span', itemprop="addressLocality").string
        park_state = soup.find('span', itemprop="addressRegion").string
        self.address = park_city+', '+park_state
        if soup.find('span', class_="postal-code"):
            self.zipcode = soup.find('span', class_="postal-code").string
        else:
            self.zipcode = soup.find('span', itemprop="postalCode").string #Found a sit where it was postalCode instead of postal-code and itemprop instead of class
        self.phone = soup.find('span', class_="tel").string.strip()
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    nps_url = BASE_URL
    url_text = make_url_request_using_cache(nps_url, CACHE_DICT)
    #response = requests.get(nps_url) #Withput Caching

    soup = BeautifulSoup(url_text, 'html.parser') #With Caching

    find_a_state = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch")
    states_results = find_a_state.find_all('li', recursive=False)
    states_list = []
    for li in states_results:
        states_list.append(li.string.lower())
    nps_home = "https://www.nps.gov"
    states_url_list = []
    for link in find_a_state.find_all('a'):
        state_url = nps_home+link.get('href')
        states_url_list.append(state_url)
    state_url_dict = {}
    for i in range(len(states_list)):
        state_url_dict[states_list[i]] = states_url_list[i]
    return(state_url_dict)


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    return NationalSite(url=site_url)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    parent_url = 'https://www.nps.gov'
    url_text = make_url_request_using_cache(state_url, CACHE_DICT) 
    #response = requests.get(state_url) #Without Caching
    listy = []
    objects_list = []
    soup = BeautifulSoup(url_text, 'html.parser') #With Caching
    for link in soup.find_all('div', class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left"):
        for i in link.find_all('a'):
            url_state = (i.get("href"))
            full_url = parent_url+url_state+'index.htm'
            listy.append(full_url)
    for item in listy:
        objects_list.append(NationalSite(item))
    return objects_list

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    endpoint = 'http://www.mapquestapi.com/search/v2/radius'
    param = {
    'key' : secret.API_KEY,
    'origin' : site_object.zipcode,
    'radius' : '10',
    'maxMatches' : '10',
    'ambiguities' : 'ignore',
    'outFormat' : 'json'
    }
    api_url = endpoint+'?key='+param['key']+'&origin='+param['origin'].strip()+'&radius='+param['radius']+'&maxMatches='+param['maxMatches']+'&ambiguities='+param['ambiguities']+'&outFormat='+param['outFormat']
    # response_new = requests.get(api_url) #Without Caching
    url_text = make_url_request_using_cache(api_url, CACHE_DICT) #With Caching
    map_str = url_text
    map_json = json.loads(map_str)
    return map_json

if __name__ == "__main__":
    
    state_dict = build_state_url_dict()
    state_query = input("Enter the name of a state (e.g. Michigan, michigan) or 'exit': ")
    while True:
        if state_query.lower() == 'exit':
            quit()
        elif state_query.lower() in state_dict.keys():
            state_url = state_dict[state_query.lower()]
            site_object_list = get_sites_for_state(state_url)
            print('----------------------------------------')
            print(f'List of National Sites in {state_query}')
            print('----------------------------------------')
            for i in range(len(site_object_list)):
                print(f'[{i + 1}] {site_object_list[i].info()}')
            while True:
                new_query = input("Choose the number for detail search or 'exit' or 'back': ")
                if new_query.lower() == 'back':
                    state_query = input("Enter the name of a state (e.g. Michigan, michigan) or 'exit': ")
                    break
                elif new_query.lower() == 'exit':
                    quit()
                elif new_query.isnumeric():
                    new_query_integer = int(new_query)
                    # if new_query_integer in range(start=1,stop=(len(site_object_list)+1)):
                    if new_query_integer > 0 and new_query_integer <= len(site_object_list):
                        print("---------------------------------------------------")
                        print(f"Places near {site_object_list[new_query_integer-1].name}")
                        print("---------------------------------------------------")
                        map_json = get_nearby_places(site_object_list[new_query_integer-1])
                        for i in map_json['searchResults']:
                            nearby_name = i['name']
                            if i['fields']['group_sic_code_name_ext']:
                                nearby_category = i['fields']['group_sic_code_name_ext']
                            else:
                                nearby_category = 'No Category'
                            if i['fields']['address']:
                                nearby_address = i['fields']['address']
                            else:
                                nearby_address = 'No Address'
                            if i['fields']['city']:
                                nearby_city = i['fields']['city']
                            else:
                                nearby_city = 'No City'
                            print(f'- {nearby_name} ({nearby_category}): {nearby_address}, {nearby_city}')
                    else:
                        print("Invalid Input")
                        new_query = input("Choose the number for detail search or 'exit' or 'back': ")
                        break
                else:
                    print("[Error] Invalid Input")
                    new_query = input("Choose the number for detail search or 'exit' or 'back': ")
        else:
            state_query = input("[Error] Please input a proper state name: ")

