from bs4 import BeautifulSoup as Soup
import urllib.request
import requests
from pandas import DataFrame
import re

from flask import Flask, render_template, request, Response
from flask_cors import cross_origin

app = Flask(__name__)
df: DataFrame


class DataCollection:
    def __init__(self):
        self.data = {"Product": list(),
                     "Name": list(),
                     "Price": list(),
                     "Rating": list(),
                     "Comment Heading": list(),
                     "Comment": list()}

    def get_final_data(self, comment_box=None, prod_name=None, prod_price=None, vendor=None):

        self.data["Product"].append(prod_name)
        self.data["Price"].append(prod_price)
        if vendor == 'flipkart':
            try:
                self.data["Name"].append(comment_box.div.div.find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text)
            except:
                self.data["Name"].append('No Name')

            try:
                self.data["Rating"].append(comment_box.div.div.div.div.text)
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.div.div.div.p.text)
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                comment_tag = comment_box.div.div.find_all('div', {'class': ''})
                self.data["Comment"].append(comment_tag[0].div.text)
            except:
                self.data["Comment"].append('')

        elif vendor == 'walmart':
            try:
                self.data['Name'].append(comment_box.find('span', {'class': 'review-footer-userNickname'}).text)
            except:
                self.data["Name"].append('No Name')

            try:
                self.data["Rating"].append(
                    comment_box.find('span', {'class': 'average-rating'}).text.replace('(', '').replace(')', ''))
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.find('h3', {'class': 'review-title font-bold'}).text)
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                self.data["Comment"].append(comment_box.find('div', {'class': 'review-text'}).text)
            except:
                self.data["Comment"].append('')

        else:
            try:
                self.data["Name"].append(comment_box.div.a.div.next_sibling.text)
            except:
                self.data["Name"].append('No Name')

            try:
                self.data["Rating"].append(comment_box.div.next_sibling.a.text.replace('.0 out of 5 stars', ''))
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.div.next_sibling.a.next_sibling.next_sibling.span.text)
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                comment_tag = comment_box.div.next_sibling.next_sibling.next_sibling.next_sibling.span.div.div.span
                self.data["Comment"].append(comment_tag.text.replace('\n', ''))
            except:
                self.data["Comment"].append('')

    def get_main_html(self, base_url=None, search_string=None, vendor=None):
        if vendor == 'flipkart':
            search_url = f"{base_url}/search?q={search_string}"
        elif vendor == 'walmart':
            search_url = f"{base_url}/search/?query={search_string}"
        else:
            search_url = f"{base_url}/s?k={search_string}"

        if vendor == 'walmart':
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/86.0.4240.183 Safari/537.36"}
            with requests.get(search_url, headers=headers) as page:
                # print(Soup(page.content, "html.parser").body.text)
                return Soup(page.content, "html.parser")
        else:
            with urllib.request.urlopen(search_url) as url:
                page = url.read()
            # print(Soup(page, "html.parser").prettify())
            return Soup(page, "html.parser")

    def get_product_name_links(self, base_url=None, big_boxes=None):
        temp = []
        for box in big_boxes:
            if base_url == 'https://www.walmart.com':
                try:
                    id = re.findall(re.compile(r'\/\d{9}'), box.a['href'])[0]
                    temp.append((box.img['alt'],
                                 'https://www.walmart.com/reviews/product' + id))
                except:
                    pass
            else:
                try:
                    temp.append((box.img['alt'],
                                 base_url + box["href"]))
                except:
                    pass

        return temp

    def get_prod_html(self, prod_link=None):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
                       "Accept-Encoding": "gzip, deflate",
                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT": "1",
                       "Connection": "close",
                       "Upgrade-Insecure-Requests": "1"}
            prod_page = requests.get(prod_link, headers=headers)
            return Soup(prod_page.content, "html.parser")

    def get_data_dict(self):
        return self.data


@app.route('/', methods=['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")


@app.route('/review', methods=("POST", "GET"))
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            vendor = request.form['shop']
            if vendor == 'flipkart':
                base_url = 'https://www.flipkart.com'
            elif vendor == 'walmart':
                base_url = 'https://www.walmart.com'
            else:
                base_url = 'https://www.amazon.in'

            search_string = request.form['query']

            search_string = search_string.replace(" ", "+")

            get_data = DataCollection()

            query_html = get_data.get_main_html(base_url, search_string, vendor)

            if vendor == 'flipkart':
                big_boxes = query_html.find_all("a", {"href": re.compile(r"\/.+\/p\/.+qH=.+")})
            elif vendor == 'walmart':
                big_boxes = query_html.find_all('div', {'class': 'search-result-gridview-item clearfix arrange-fill'})
                # print(len(big_boxes))
            else:
                big_boxes = query_html.find_all("a", {"class": "a-link-normal s-no-outline",
                                                      'href': re.compile(r'\/.+\/dp\/.+?dchild=1.*')})

            product_name_links = get_data.get_product_name_links(base_url, big_boxes)
            for prod_name, prod_link in product_name_links[:4]:
                for prod_HTML in get_data.get_prod_html(prod_link):
                    try:
                        print(prod_link)
                        prod_price = ''
                        if vendor == 'flipkart':
                            comment_boxes = prod_HTML.find_all('div', {'class': '_16PBlm'})
                            prod_price = prod_HTML.find_all('div', {"class": "_30jeq3 _16Jk6d"})[0].text

                        elif vendor == 'walmart':
                            comment_boxes = prod_HTML.find_all('div', {'itemprop': 'review'})
                            prod_price = prod_HTML.find('span', {'class': 'price-group'}).text
                            # print(f"{len(comment_boxes)}  {prod_price}")
                        else:
                            comment_boxes = prod_HTML.find_all('div', {'id': re.compile(r'customer_review-.+')})
                            try:
                                container = prod_HTML.find_all('td', {"class": "a-span12"})
                                container = Soup(str(container), 'html.parser')
                                prod_price = container.find_all('span', {"id": "priceblock_ourprice"})[0].text
                            except:
                                prod_price = prod_HTML.find_all('span', {"class": "a-size-base a-color-price"})[0].text
                        if vendor == 'walmart':
                            prod_price = float((prod_price.replace("$", "")).replace(",", "").replace(" ", ""))
                        else:
                            prod_price = float((prod_price.replace("₹", "")).replace(",", "").replace(" ", ""))
                        # print(prod_price)
                        for comment_box in comment_boxes:
                            get_data.get_final_data(comment_box, prod_name, prod_price, vendor)

                    except:
                        pass

            global df
            df = DataFrame(get_data.get_data_dict())

            return render_template('review.html',
                                   tables=[df.to_html(classes='data')],
                                   titles=df.columns.values,
                                   search_string=search_string,
                                   )
        except Exception as e:
            print(e)
            return render_template("404.html")

    else:
        return render_template("index.html")


@app.route("/getCSV")
def get_csv():
    global df
    return Response(
        df.to_csv(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment;filename=review.csv"})


if __name__ == '__main__':
    app.run(debug=True)
