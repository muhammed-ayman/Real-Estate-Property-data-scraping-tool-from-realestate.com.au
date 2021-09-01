import requests
import re
import json
from bs4 import BeautifulSoup
import sqlite3
from pprint import pprint

class DataBase():

    def __init__(self):
        self.conn = sqlite3.connect('realestate.db')
        self.cursor = self.conn.cursor()

    def create_realestate_table(self):
        self.cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='realestate'")
        if self.cursor.fetchone()[0]:
            self.conn.commit()
            return
        self.cursor.execute("""CREATE TABLE realestate (
                    product_id text,
                    product_link text,
                    product_main_image text,
                    product_beds text,
                    product_price text,
                    product_land_size text,
                    product_street text,
                    product_suburb text
                )""")
        self.conn.commit()

    def insert_product_data(self,id,link,image_link,beds,price,land_size,street,suburb):
        self.cursor.execute(f"INSERT INTO realestate VALUES (?,?,?,?,?,?,?,?)", (id,link,image_link,beds,price,land_size,street,suburb))
        self.conn.commit()

    def check_product(self,link):
        self.cursor.execute(f"SELECT * FROM realestate WHERE product_link = '{link}'")
        if len(self.cursor.fetchall()) > 0:
            self.conn.commit()
            return True
        return False

    def list_products(self):
        self.cursor.execute('SELECT * FROM realestate')
        return self.cursor.fetchall()

class RealStateSiteScraper():

    def __init__(self, headers):
        self.headers = headers
        self.products = []

    def scrape(self):
        self.products = []
        current_page = 1

        while True:
            url = f'https://www.realestate.com.au/buy/property-house-with-3-bedrooms-size-400-in-halls+head,+wa+6210/list-{current_page}?activeSort=list-date'
            request = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(request.content, 'html.parser')
            articles = soup.find_all(attrs={'data-testid' : "ResidentialCard"})
            script_blocks = soup.find_all('script', {'type': 'text/javascript'})

            if len(articles) == 0:
                break

            true=false=null=1
            REA_lexaCache = eval(re.search('(?<=REA.lexaCache = )(.*)(?=\n)',request.text)[0])

            for article in articles:
                article_link = f"https://www.realestate.com.au{article.find_all(attrs={'class':'details-link'})[0]['href']}"
                article_id = article_link.split('-')[-1]
                article_main_image = REA_lexaCache[f'$BuyResidentialListing{article_id}.media.mainImage']['templatedUrl'].replace("{size}","800x600")
                article_address_parent = article.find_all(attrs={'class':'details-link residential-card__details-link'})[0]
                article_address = article_address_parent.find_all('span')[0].text.split(', ')
                article_beds = article.find_all(attrs={'class':'general-features__icon general-features__beds'})[0].text.replace(' ', '')
                article_price = article.find_all(attrs={'class':'property-price'})[0].text
                article_land_size = f"{article.find_all(attrs={'class':'property-size'})[0]['aria-label'].split()[0]} m^2"

                product = {
                    'product_id' : article_id,
                    'product_link' : article_link,
                    'product_main_image' : article_main_image,
                    'product_beds' : article_beds,
                    'product_price' : article_price,
                    'product_land_size' : article_land_size,
                    'product_street' : article_address[0],
                    'product_suburb' : article_address[1]
                }

                self.products.append(product)

            current_page += 1

        return self.products

    def save_data(self,db):
        for product in self.products:
            if not db.check_product(product['product_link']):
                db.insert_product_data(product['product_id'],product['product_link'],product['product_main_image'],product['product_beds'],product['product_price'],product['product_land_size'],product['product_street'],product['product_suburb'])

# The cookies need to be updated manually

headers = {
    'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'cookie': 'reauid=65af67d4cc44000080c722617f030000fdbe0100; split_audience=e; _gcl_au=1.1.1624509983.1629669255; mid=3875071160449194918; s_ecid=MCMID%7C34279370637516792610447471658719206757; VT_LANG=language%3Den-US; _fbp=fb.2.1629669260268.1141311736; id5id.1st=%20%7B%20%22created_at%22%3A%20%222021-08-22T21%3A54%3A20.31093Z%22%2C%20%22id5_consent%22%3A%20true%2C%20%22original_uid%22%3A%20%22ID5-ZHMOlf2Nf2kDjqRW8grlEkRy_csfrpm1oTqvggz-6Q!ID5*72gEWyDdxGvcI8ew49JD8adkO-l-P-eNAIFzuzcst_0AAE-0pgnaJX8oMrtrtsgK%22%2C%20%22universal_uid%22%3A%20%22ID5-ZHMO4sMhqSkNh7ZUW2hELwiN1fKkATDXQxe0gEgj8A!ID5*YoNHvtoIK1gRxo1HbJBitRfDhyTKbwvB74gdRbiDKQEAADB9YZLIz0veq-mvS5Hw%22%2C%20%22signature%22%3A%20%22ID5_Ac9xm1mTMovpSPUtgVcCicEgSt0e5jjDzja8xJsNL_CXsqfWQ8IdZhVkkTo7rZ_pDAd9ch3H5ecTnlBmeqhJDww%22%2C%20%22link_type%22%3A%202%2C%20%22cascade_needed%22%3A%20true%2C%20%22privacy%22%3A%20%7B%20%22jurisdiction%22%3A%20%22other%22%2C%20%22id5_consent%22%3A%20true%7D%7D; id5id.1st_last=1629669260699; id5id.1st_123_nb=1; mako_fpc_id=93034fa9-c8dd-45d5-80de-795a623af0a8; _gid=GA1.3.1099597143.1629825811; s_nr=1629827901196; Country=EG; fullstory_audience_split=B; AMCVS_341225BE55BBF7E17F000101%40AdobeOrg=1; s_cc=true; s_sq=%5B%5BB%5D%5D; AMCV_341225BE55BBF7E17F000101%40AdobeOrg=-330454231%7CMCIDTS%7C18866%7CMCMID%7C34279370637516792610447471658719206757%7CMCAAMLH-1630555378%7C6%7CMCAAMB-1630555378%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1629957778s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C3.1.2; ab.storage.deviceId.746d0d98-0c96-45e9-82e3-9dfa6ee28794=%7B%22g%22%3A%224df2d0bf-eb63-599f-61bf-0b8e513215b7%22%2C%22c%22%3A1629835050677%2C%22l%22%3A1629950578832%7D; _sp_ses.2fe7=*; QSI_HistorySession=https%3A%2F%2Fwww.realestate.com.au%2Fproperty-house-wa-halls%2Bhead-137096610~1629946110460%7Chttps%3A%2F%2Fwww.realestate.com.au%2Fbuy%2Fproperty-house-with-3-bedrooms-size-400-in-halls%2Bhead%2C%2Bwa%2B6210%2Flist-1%3FactiveSort%3Dlist-date~1629950601976%7Chttps%3A%2F%2Fwww.realestate.com.au%2Fbuy%2Fproperty-house-with-3-bedrooms-size-400-in-halls%2Bhead%2C%2Bwa%2B6210%2Flist-18%3FactiveSort%3Dlist-date~1629950609630; KP2_UIDz-ssn=0DEXqrKVsqTEFSNh9Nh8dTVyZ1rj31WtNy2DSdiqRQaBDBKNszSo4ABZIdsJXbjVGPme2vIN322zFTpXBxlOLEgn397QaUaFZ2AgmEpFYO8hT5y30AOMKE3wIb7yh6owfaIH4I3387keW3VBaP1TF8hOo; KP2_UIDz=0DEXqrKVsqTEFSNh9Nh8dTVyZ1rj31WtNy2DSdiqRQaBDBKNszSo4ABZIdsJXbjVGPme2vIN322zFTpXBxlOLEgn397QaUaFZ2AgmEpFYO8hT5y30AOMKE3wIb7yh6owfaIH4I3387keW3VBaP1TF8hOo; pageview_counter.srs=10; utag_main=v_id:017b6fdb5f45000235479836162003073008e06b00978$_sn:11$_se:10$_ss:0$_st:1629953169357$vapi_domain:realestate.com.au$dc_visit:11$ses_id:1629950576532%3Bexp-session$_pn:4%3Bexp-session$dc_event:4%3Bexp-session$dc_region:ap-southeast-2%3Bexp-session; _sp_id.2fe7=b13a769b-50da-466a-8980-647561ef5223.1629669255.11.1629951370.1629946120.0da54d59-8242-4cdd-8bd9-e364a767097f; ab.storage.sessionId.746d0d98-0c96-45e9-82e3-9dfa6ee28794=%7B%22g%22%3A%220252d5f1-150e-0550-a4bf-476706bc396e%22%2C%22e%22%3A1629953171193%2C%22c%22%3A1629950578831%2C%22l%22%3A1629951371193%7D; _ga_F962Q8PWJ0=GS1.1.1629950578.11.1.1629951370.0; _ga=GA1.3.895227331.1629669255; cto_bundle=3Fu6M191VEJYOVVId0pEMVRXNSUyQjNJM280dkxEbHI5RVAlMkJ4RG1YT2E5d3FHaXFwakRhYWc0MzFTY2JjM3pVWGZBQmtwcEJjJTJCaWp2WDZLd0ZERFd3R2cyRVZDQWJxNnRuQWh6JTJCbnIyZllIQXMlMkZBZ2RiZDl5R3lCeUpUUEhqaDU3QWM5UzVxenpIZndUMEZJWk5kSWhHM050SHZBJTNEJTNE; External=%2FAPPNEXUS%3D1029589641736962498%2FCASALE%3DYRAcopx9D9-T0NaIEtDozgAA%25261833%2FOPENX%3D845f8ae8-b54a-43ab-a142-7c2196bfc3e3%2FPUBMATIC%3D311F77E0-6069-43C6-8873-99DD545F383E%2FRUBICON%3DKS3IMA8Z-T-7WMW%2FTRIPLELIFT%3D7920900161920461310%2F_EXP%3D1661486609%2F_exp%3D1661487373',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
}

if __name__ == '__main__':
    db = DataBase()
    db.create_realestate_table()
    scraper = RealStateSiteScraper(headers)
    scraper.scrape()
    scraper.save_data(db)
    pprint(db.list_products())
