'''import urllib.request
from bs4 import BeautifulSoup

query = 'mobiles'
page = urllib.request.urlopen(f'http://flipkart.com/search?q={query}')
soupy = BeautifulSoup(page.read(),'html.parser')
container = soupy.find_all("a", {"class": "_31qSD5"}, href=True)
for x in container:
    print(x['href'])'''
from bs4 import BeautifulSoup as soup
import urllib
import requests
import pandas as pd

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

	def get_final_data(self, commentbox=None, prodName=None, prod_price=None):
		'''
		this will append data gathered from comment box into data dictionary
		'''
		self.data["Product"].append(prodName)
		self.data["Price (INR)"].append(prod_price)
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

	def get_main_HTML(self, base_URL=None, search_string=None):
		'''
		return main html page based on search string
		'''
		search_url = f"{base_URL}/search?q={search_string}"
		with urllib.request.urlopen(search_url) as url:
			page = url.read()
		return soup(page, "html.parser")

	def get_product_name_links(self, flipkart_base=None, bigBoxes=None):
		temp = []
		for box in bigBoxes:
			try:
				temp.append((box.div.div.div.a.img['alt'],
					flipkart_base + box.div.div.div.a["href"]))
			except:
				pass
			
		return temp

	def get_prod_HTML(self, productLink=None):
		prod_page = requests.get(productLink)
		return soup(prod_page.text, "html.parser")


	def get_data_dict(self):
		return self.data

@app.route('/',methods=['GET'])  
@cross_origin()
def homePage():
	return render_template("index.html")

# route to display the review page
@app.route('/review', methods=("POST", "GET"))
@cross_origin()
def index():
	if request.method == 'POST':
		try:
			base_URL = 'https://www.flipkart.com'
			
			search_string = request.form['query']
			
			search_string = search_string.replace(" ", "+")
			print('processing...')

			get_data = DataCollection()

			flipkart_HTML = get_data.get_main_HTML(base_URL, search_string)

			bigBoxes = flipkart_HTML.find_all("div", {"class":"bhgxx2 col-12-12"})

			product_name_Links = get_data.get_product_name_links(base_URL, bigBoxes)

			for prodName, productLink in product_name_Links[:4]:
				for prod_HTML in get_data.get_prod_HTML(productLink):
					try:
						comment_boxes = prod_HTML.find_all('div', {'class': '_3nrCtb'})

						prod_price = prod_HTML.find_all('div', {"class": "_1vC4OE _3qQ9m1"})[0].text
						prod_price = float((prod_price.replace("₹", "")).replace(",", ""))
						for commentbox in comment_boxes:
							get_data.get_final_data(commentbox, prodName, prod_price)
							
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
			# return 404 page if error occurs 
			return render_template("404.html")

	else:
		# return index page if home is pressed or for the first run
		return render_template("index.html")

if __name__ == '__main__':
	app.run(debug=True)