from bs4 import BeautifulSoup as soup
import urllib
import requests
import pandas as pd
import re

from flask import Flask, render_template,  session, redirect, request
from flask_cors import CORS,cross_origin

app = Flask(__name__)

class DataCollection:
	def __init__(self):
		self.data = {"Product": list(), 
		"Name": list(),
		"Price (INR)": list(), 
		"Rating": list(), 
		"Comment Heading": list(), 
		"Comment": list()}

	def get_final_data(self, commentbox=None, prodName=None, prod_price=None, vendor=None):
		
		self.data["Product"].append(prodName)
		self.data["Price (INR)"].append(prod_price)
		if vendor == 'flipkart':
			try:
				self.data["Name"].append(commentbox.div.div.\
					find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text)
			except:
				self.data["Name"].append('No Name')

			try:
				self.data["Rating"].append(commentbox.div.div.div.div.text)
			except:
				self.data["Rating"].append('No Rating')

			try:
				self.data["Comment Heading"].append(commentbox.div.div.div.p.text)
			except:
				self.data["Comment Heading"].append('No Comment Heading')

			try:
				comtag = commentbox.div.div.find_all('div', {'class': ''})
				self.data["Comment"].append(comtag[0].div.text)
			except:
				self.data["Comment"].append('')	
		
		else:
			try:
				self.data["Name"].append(commentbox.div.a.div.next_sibling.text)
			except:
				self.data["Name"].append('No Name')

			try:
				self.data["Rating"].append(commentbox.div.next_sibling.a.text.replace('.0 out of 5 stars',''))
			except:
				self.data["Rating"].append('No Rating')

			try:
				self.data["Comment Heading"].append(commentbox.div.next_sibling.a.next_sibling.next_sibling.span.text)
			except:
				self.data["Comment Heading"].append('No Comment Heading')

			try:
				comtag = commentbox.div.next_sibling.next_sibling.next_sibling.next_sibling.span.div.div.span
				self.data["Comment"].append(comtag.text.replace('\n',''))
			except:
				self.data["Comment"].append('')


	def get_main_HTML(self, base_URL=None, search_string=None, vendor=None):
		if vendor == 'flipkart':
			search_url = f"{base_URL}/search?q={search_string}"
		else:
			search_url = f"{base_URL}/s?k={search_string}"

		with urllib.request.urlopen(search_url) as url:
			page = url.read()
		return soup(page, "html.parser")

	def get_product_name_links(self, base_URL=None, bigBoxes=None):
		temp = []
		for box in bigBoxes:
			try:
				temp.append((box.img['alt'],
					base_URL + box["href"]))
				#print(f"{box.img['alt']} : {base_URL + box['href']}")
			except:
				pass
			
		return temp

	def get_prod_HTML(self, productLink=None):
		headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
		 "Accept-Encoding":"gzip, deflate",
		 "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close",
		  "Upgrade-Insecure-Requests":"1"}
		prod_page = requests.get(productLink,headers=headers)
		return soup(prod_page.text, "html.parser")


	def get_data_dict(self):
		return self.data

@app.route('/',methods=['GET'])  
@cross_origin()
def homePage():
	return render_template("index.html")

@app.route('/review', methods=("POST", "GET"))
@cross_origin()
def index():
	if request.method == 'POST':
		try:
			vendor = request.form['shop']
			if vendor == 'flipkart':
				base_URL = 'https://www.flipkart.com'
			else:
				base_URL = 'https://www.amazon.in'
			
			search_string = request.form['query']
			
			search_string = search_string.replace(" ", "+")
			print('processing...')

			get_data = DataCollection()

			query_HTML = get_data.get_main_HTML(base_URL, search_string, vendor)

			if vendor=='flipkart':
				bigBoxes = query_HTML.find_all("a", {"href":re.compile(r"\/.+\/p\/.+qH=.+")})
			else:
				bigBoxes = query_HTML.find_all("a", {"class": "a-link-normal s-no-outline", 
													'href': re.compile(r'\/.+\/dp\/.+?dchild=1.*')})
			
			product_name_Links = get_data.get_product_name_links(base_URL, bigBoxes)
			for prodName, productLink in product_name_Links[:4]:
				print(productLink)
				for prod_HTML in get_data.get_prod_HTML(productLink):
					try:
						prod_price = ''
						if vendor == 'flipkart':
							comment_boxes = prod_HTML.find_all('div', {'class': '_3nrCtb'})
							prod_price = prod_HTML.find_all('div', {"class": "_1vC4OE _3qQ9m1"})[0].text
							
						else:
							comment_boxes = prod_HTML.find_all('div', {'id':re.compile(r'customer_review-.+')})
							try:
								container = prod_HTML.find_all('td', {"class": "a-span12"})
								container = soup(str(container),'html.parser')
								prod_price = container.find_all('span', {"id": "priceblock_ourprice"})[0].text
							except:
								prod_price = prod_HTML.find_all('span', {"class": "a-size-base a-color-price"})[0].text

						#print(prod_price)
						prod_price = float((prod_price.replace("₹", "")).replace(",", "").replace(" ",""))
						for commentbox in comment_boxes:
							get_data.get_final_data(commentbox, prodName, prod_price, vendor)
							
					except:
						pass

			df = pd.DataFrame(get_data.get_data_dict())
			
			return render_template('review.html', 
			tables=[df.to_html(classes='data')],
			titles=df.columns.values,
			search_string = search_string,
			)
		except Exception as e:
			print(e)
			return render_template("404.html")

	else:
		return render_template("index.html")

if __name__ == '__main__':
	app.run(debug=True)