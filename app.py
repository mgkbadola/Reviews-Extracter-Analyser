import os
import re
import urllib.request

import matplotlib
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup as Soup
from flask import Flask, render_template, request, Response
from flask_cors import cross_origin
from flask_ngrok import run_with_ngrok
from pandas import DataFrame
from wordcloud import WordCloud, STOPWORDS

wd = 'D:/IDEAProjects/Py/TOC-Innovative-Work-Project/static/'
IMG_FOLDER = wd + 'images/'
CSV_FOLDER = wd + 'CSVs/'
app = Flask(__name__)
run_with_ngrok(app=app)
df: DataFrame

app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['CSV_FOLDER'] = CSV_FOLDER


class DataCollection:
    def __init__(self):
        self.data = {"Product": list(),
                     "Name": list(),
                     "Price": list(),
                     "Rating": list(),
                     "Comment Heading": list(),
                     "Comment": list()}

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
                return Soup(page.content, "html.parser")
        else:
            with urllib.request.urlopen(search_url) as url:
                page = url.read()
            # print(Soup(page, "html.parser").prettify())
            return Soup(page, "html.parser")

    def get_prod_html(self, product_link=None):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
                   "Accept-Encoding": "gzip, deflate",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT": "1",
                   "Connection": "close",
                   "Upgrade-Insecure-Requests": "1"}
        prod_page = requests.get(product_link, headers=headers)
        return Soup(prod_page.content, "html.parser")

    def get_product_name_links(self, base_url=None, big_boxes=None):
        temp = []
        for box in big_boxes:
            if base_url == 'https://www.walmart.com':
                try:
                    temp.append((box.img['alt'],
                                 "https://www.walmart.com/reviews/product" + box.a['href'] + '?sort=rating-asc'))
                except:
                    pass
            elif base_url == 'https://www.flipkart.com':
                link = re.findall(re.compile(r'\/.+\/p\/.+\?pid=.{16}&lid=.{25}'),
                                  box['href'])[0]
                link = link.replace('/p/', '/product-reviews/')
                link += '&aid=overall&certifiedBuyer=true&sortOrder=NEGATIVE_FIRST'
                temp.append((box.img['alt'],
                             base_url + link))
                # print(base_url + link)
            else:
                try:
                    temp.append((box.img['alt'],
                                 base_url + box["href"]))
                except:
                    pass

        return temp

    def get_final_data(self, comment_box=None, prod_name=None, prod_price=None, vendor=None):

        self.data["Product"].append(prod_name)
        self.data["Price"].append(prod_price)
        if vendor == 'flipkart':
            try:
                self.data["Name"].append(comment_box.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text)
            except:
                self.data["Name"].append('No Name')

            try:
                try:
                    self.data["Rating"].append(comment_box.find_all('div', {'class': '_3LWZlK _1BLPMq'})[0].text)
                except:
                    self.data["Rating"].append(
                        comment_box.find_all('div', {'class': '_3LWZlK _1rdVr6 _1BLPMq'})[0].text)
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.find_all('p', {'class': '_2-N8zT'})[0].text)
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                self.data["Comment"].append(comment_box.find_all('div', {'class': 't-ZTKy'})[0].text
                                            .replace('READ MORE', ''))
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
                self.data["Name"].append(comment_box.find_all('span', {'class': 'a-profile-name'})[0].text)
            except:
                self.data["Name"].append('No Name')

            try:
                self.data["Rating"].append(comment_box.find_all('span', {'class': 'a-icon-alt'})[0]
                                           .text.replace('.0 out of 5 stars', ''))
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.find_all('a', {'data-hook': 'review-title'})[0].text
                                                    .replace('\n', ''))
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                self.data["Comment"].append(comment_box.find_all('span', {'data-hook': 'review-body'})[0].text
                                            .replace('\n', ''))
            except:
                self.data["Comment"].append('')

    def get_data_dict(self):
        return self.data

    def save_as_dataframe(self, dataframe, file_name=None):
        # save the CSV file to CSVs folder
        csv_path = app.config['CSV_FOLDER'] + file_name
        fileExtension = '.csv'
        final_path = f"{csv_path}{fileExtension}"
        # clean previous files -
        CleanCache(directory=app.config['CSV_FOLDER'])
        # save new csv to the csv folder
        dataframe.to_csv(final_path, index=None)
        print("File saved successfully!!")
        return final_path

    def save_wordcloud_image(self, dataframe=None, img_file_name=None):
        # extract all the comments
        txt = dataframe["Comment"].values
        # generate the word cloud
        wc = WordCloud(width=800, height=400, background_color='black', stopwords=STOPWORDS).generate(str(txt))
        matplotlib.use('agg')

        plt.figure(figsize=(20, 10), facecolor='k', edgecolor='k')
        plt.imshow(wc, interpolation='bicubic')
        plt.axis('off')
        plt.tight_layout()
        # create path to save wc image
        image_path = app.config['IMG_FOLDER'] + img_file_name + '.png'
        # Clean previous image from the given path
        CleanCache(directory=app.config['IMG_FOLDER'])
        # save the image file to the image path
        plt.savefig(image_path)
        plt.close()
        print("saved wc")


class CleanCache:
    def __init__(self, directory=None):
        self.clean_path = directory
        # only proceed if directory is not empty
        if os.listdir(self.clean_path) != list():
            # iterate over the files and remove each file
            files = os.listdir(self.clean_path)
            for file_name in files:
                print(file_name)
                os.remove(self.clean_path + file_name)
        print("cleaned!")


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
                big_boxes = query_html.find_all('div', {'data-type': 'items'})
                if len(big_boxes) == 0:
                    big_boxes = query_html.find('div', {'data-tl-id': re.compile(r"ProductTileListView-\d{1,2}")})
            else:
                big_boxes = query_html.find_all("a", {"class": "a-link-normal s-no-outline",
                                                      'href': re.compile(r'\/.+\/dp\/.+?dchild=1.*')})

            product_name_links = get_data.get_product_name_links(base_url, big_boxes)
            for prod_name, product_link in product_name_links[:4]:
                for prod_html in get_data.get_prod_html(product_link):
                    try:
                        prod_price = ''
                        if vendor == 'flipkart':
                            comment_boxes = prod_html.find_all('div', {'class': '_27M-vq'})
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101"
                                                     " Firefox/66.0",
                                       "Accept-Encoding": "gzip, deflate",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                       "DNT": "1",
                                       "Connection": "close",
                                       "Upgrade-Insecure-Requests": "1"}
                            positive_link = product_link.replace('NEGATIVE', 'POSITIVE')
                            prod_page = requests.get(positive_link, headers=headers)
                            prod_positive = Soup(prod_page.content, "html.parser")
                            comment_boxes += prod_positive.find_all('div', {'class': '_27M-vq'})
                            prod_price = prod_positive.find_all('div', {"class": "_30jeq3"})[0].text

                        elif vendor == 'walmart':
                            comment_boxes = prod_html.find_all('div', {'class': 'Grid-col customer-review-body'})
                            positive_link = product_link.replace('asc', 'desc')
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101"
                                                     " Firefox/66.0",
                                       "Accept-Encoding": "gzip, deflate",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                       "DNT": "1",
                                       "Connection": "close",
                                       "Upgrade-Insecure-Requests": "1"}
                            prod_page = requests.get(positive_link, headers=headers)
                            prod_positive = Soup(prod_page.content, "html.parser")
                            comment_boxes += prod_positive.find_all('div', {'class': 'Grid-col customer-review-body'})
                            prod_price = prod_html.find('span', {'class': 'price-group'}).text
                        else:
                            try:
                                container = prod_html.find_all('td', {"class": "a-span12"})
                                container = Soup(str(container), 'html.parser')
                                prod_price = container.find_all('span', {"id": "priceblock_ourprice"})[0].text
                            except:
                                prod_price = prod_html.find_all('span', {"class": "a-size-base a-color-price"})[0].text
                            # print(prod_price)
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101"
                                                     " Firefox/66.0",
                                       "Accept-Encoding": "gzip, deflate",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                       "DNT": "1",
                                       "Connection": "close",
                                       "Upgrade-Insecure-Requests": "1"}
                            link = product_link
                            link = re.findall(re.compile(r'\/.+\/.{10}'), link)[0]
                            link = link.replace('dp', 'product-reviews')
                            link = 'https:' + link + '/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8' \
                                                     '&reviewerType=avp_only_reviews&pageNumber=1&filterByStar=critical'
                            # print(link)
                            prod_page = requests.get(link, headers=headers)
                            prod_negative = Soup(prod_page.content, 'html.parser')
                            comment_boxes = prod_negative.find_all('div', {'id': re.compile(r'customer_review-.+')})
                            link = link.replace('critical', 'positive')
                            prod_page = requests.get(link, headers=headers)
                            prod_positive = Soup(prod_page.content, 'html.parser')
                            comment_boxes += prod_positive.find_all('div', {'id': re.compile(r'customer_review-.+')})
                            # print(len(comment_boxes))

                        if vendor == 'walmart':
                            prod_price = float((prod_price.replace("$", "")).replace(",", "").replace(" ", ""))
                        else:
                            prod_price = float((prod_price.replace("₹", "")).replace(",", "").replace(" ", ""))
                        # print(prod_price)
                        for comment_box in comment_boxes:
                            get_data.get_final_data(comment_box, prod_name, prod_price, vendor)

                    except:
                        pass
            # save the data as gathered in dataframe
            global df
            df = DataFrame(get_data.get_data_dict())
            # save dataframe as a csv which will be availble to download
            download_path = get_data.save_as_dataframe(df, file_name=search_string.replace("+", "_"))

            # generate and save the wordcloud image
            get_data.save_wordcloud_image(df,
                                          img_file_name=search_string.replace("+", "_"))

            return render_template('review.html',
                                   tables=[df.to_html(index=False, classes='data')],
                                   titles=df.columns.values,
                                   search_string=search_string,
                                   download_csv=app.config['CSV_FOLDER']
                                   )
        except Exception as e:
            print(e)
            return render_template("404.html")

    else:
        return render_template("index.html")


@app.route("/get_csv")
def get_csv():
    global df
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-disposition":
                     f"attachment;file_name=review.csv"})


@app.route('/show')
@cross_origin()
def show_wordcloud():
    img_file = os.listdir(app.config['IMG_FOLDER'])[0]
    print()
    return render_template("show_wc.html", user_image='images/' + img_file)


if __name__ == '__main__':
    app.run()
