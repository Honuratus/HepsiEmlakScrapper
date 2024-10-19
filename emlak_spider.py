import scrapy
from openpyxl import Workbook
from scrapy.crawler import CrawlerProcess


data = []

# Örümcek sınıfını tanımlama
class EmlakSpider(scrapy.Spider):
    name = 'emlak'
    allowed_domains = ['hepsiemlak.com']

    def __init__(self, *args, **kwargs):
        super(EmlakSpider, self).__init__(*args, **kwargs)
        self.headers = set() # başlıkları tutmak için 
        self.workbook = Workbook()
        self.sheet = self.workbook.active
        self.data = []
        self.number = 0 # kaç tane veriyi çektiğini görmem için oluşturduğum değişken

    def start_requests(self):
        urls = [
            'https://www.hepsiemlak.com/buca-kiralik',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse) 

    # ilan linklerini parçalamak parçalayan method
    def parse(self, response):
        listing_links = response.css('a.card-link::attr(href)').getall()
        for link in listing_links:
            yield response.follow(link, callback=self.parse_listings)
        
        
        nextpage = response.css('a.he-pagination__navigate-text--next::attr(href)').get()
        if nextpage:
            yield response.follow(nextpage, callback=self.parse)
    
    # ilan linklerinin içinden verileri parçalayan method
    def parse_listings(self, response):
        # İlanı verilerini dictionary olarak tutmayı seçtim
        mydict = dict()
        
        # İlan başlığı verisinin çekilmesi
        title = response.css('h1.fontRB::text').get().strip()
        mydict['Ilan Baslik'] = title

        # İlan kirası verisinin çekilmesi
        price = response.css('p.fz24-text::text').get().strip()
        mydict['Ilan Kira'] = price

        spec_items = response.css('li.spec-item')
        
        # hepsi emlak sitesinde ilan sayfasında
        # başlık ve kira dışındaki verilerin çekilmesi
        for item in spec_items:
            label = item.css('span.txt::text').get()
            label = label.strip() if label else None

            value = item.css('span:not(.txt)::text').get()
            value = value.strip() if value else None

            if label and value:
                mydict[label] = value

        print(mydict)
        self.number += 1
        print(self.number)
        self.data.append(mydict)

    # Parçalama işlemi bittiğinde çağrılan method
    def closed(self, reason):
        # Her bir başlığın çekildiği sırayla gelmesi
        # ve sadece o başlıktan bir tane olması lazım
        headers = list()
        for listing in self.data:
            for key in listing.keys():
                if key not in headers:
                    headers.append(key)
        
        # openpyxl kullanılarak başlıklara excel dosyasının  başına yazıyoruz
        headers = list(headers)
        self.sheet.append(headers)
        
        # parçaladığımız verileri tutan self.data listesinden
        # her bir ilanı excel dosyasına yazıyoruz
        for listing in self.data:
            row = [listing.get(header, '') for header in headers]
            self.sheet.append(row)

        self.workbook.save('listings.xlsx')

custom_settings = {
    'CONCURRENT_REQUESTS': 1,
    'DOWNLOAD_DELAY': 3,
}

# Örümceyi çalıştırma
process = CrawlerProcess(settings=custom_settings)
process.crawl(EmlakSpider)
process.start()