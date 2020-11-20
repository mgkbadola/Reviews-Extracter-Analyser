from bs4 import BeautifulSoup as soup
import urllib
import requests
import pandas as pd
from pandas import DataFrame
import re
import os
from flask import Flask, render_template,  session, redirect, request, Response
from flask_cors import CORS, cross_origin
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import matplotlib

IMG_FOLDER = os.path.join('static', 'images')
CSV_FOLDER = os.path.join('static', 'CSVs')

app = Flask(__name__)
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

	def get_final_data(self, commentbox=None, prodName=None, prod_price=None, vendor=None):

		self.data["Product"].append(prodName)
		self.data["Price"].append(prod_price)
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

		elif vendor == 'walmart':
			try:
				self.data['Name'].append(commentbox.find('span',{'class':'review-footer-userNickname'}).text)
			except:
				self.data["Name"].append('No Name')

			try:
				self.data["Rating"].append(commentbox.find('span',{'class':'average-rating'}).text.replace('(','').replace(')',''))
			except:
				self.data["Rating"].append('No Rating')

			try:
				self.data["Comment Heading"].append(commentbox.find('h3',{'class':'review-title font-bold'}).text)
			except:
				self.data["Comment Heading"].append('No Comment Heading')

			try:
				self.data["Comment"].append(commentbox.find('div',{'class':'review-text'}).text)
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
		elif vendor == 'walmart':
			search_url = f"{base_URL}/search/?query={search_string}"
		else:
			search_url = f"{base_URL}/s?k={search_string}"

		if vendor == 'walmart':
			headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"}
			with requests.get(search_url, headers=headers) as page:
				return soup(page.content,"html.parser")
		else:
			with urllib.request.urlopen(search_url) as url:
				page = url.read()
				# print(soup(page, "html.parser").prettify())
			return soup(page, "html.parser")

	def get_product_name_links(self, base_URL=None, bigBoxes=None):
		temp = []
		for box in bigBoxes:
			if base_URL == 'https://www.walmart.com':
				try:
					temp.append((box.img['alt'],
								 "https://www.walmart.com/reviews/product" + box.a['href']))
				except:
					pass
			else:
				try:
					temp.append((box.img['alt'],
								 base_URL + box["href"]))
				except:
					pass

		return temp

	def get_prod_HTML(self, vendor=None, productLink=None):
		headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
		 "Accept-Encoding":"gzip, deflate",
		 "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close",
		  "Upgrade-Insecure-Requests":"1"}
		prod_page = requests.get(productLink, headers=headers)
		return soup(prod_page.content, "html.parser")


	def get_data_dict(self):
		return self.data

	def save_as_dataframe(self, dataframe, fileName=None):
		'''
		it saves the dictionary dataframe as csv by given filename inside
		the CSVs folder and returns the final path of saved csv
		'''
		# save the CSV file to CSVs folder
		csv_path = os.path.join(app.config['CSV_FOLDER'], fileName)
		fileExtension = '.csv'
		final_path = f"{csv_path}{fileExtension}"
		# clean previous files -
		CleanCache(directory=app.config['CSV_FOLDER'])
		# save new csv to the csv folder
		dataframe.to_csv(final_path, index=None)
		print("File saved successfully!!")
		return final_path


	def save_wordcloud_image(self, dataframe=None, img_filename=None):
		'''
		it generates and saves the wordcloud image into wc_folder
		'''
		# extract all the comments
		txt = dataframe["Comment"].values
		# generate the wordcloud
		wc = WordCloud(width=800, height=400, background_color='black', stopwords=STOPWORDS).generate(str(txt))
		matplotlib.use('agg')

		plt.figure(figsize=(20,10), facecolor='k', edgecolor='k')
		plt.imshow(wc, interpolation='bicubic') 
		plt.axis('off')
		plt.tight_layout()
		# create path to save wc image
		image_path = os.path.join(app.config['IMG_FOLDER'], img_filename + '.png')
		# Clean previous image from the given path
		CleanCache(directory=app.config['IMG_FOLDER'])
		# save the image file to the image path
		plt.savefig(image_path)
		plt.close()
		print("saved wc")


class CleanCache:
	'''
	this class is responsible to clear any residual csv and image files
	present due to the past searches made.
	'''
	def __init__(self, directory=None):
		self.clean_path = directory
		# only proceed if directory is not empty
		if os.listdir(self.clean_path) != list():
			# iterate over the files and remove each file
			files = os.listdir(self.clean_path)
			for fileName in files:
				print(fileName)
				os.remove(os.path.join(self.clean_path,fileName))
		print("cleaned!")

	
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
			elif vendor == 'walmart':
				base_URL = 'https://www.walmart.com'
			else:
				base_URL = 'https://www.amazon.in'

			search_string = request.form['query']

			search_string = search_string.replace(" ", "+")

			get_data = DataCollection()

			query_HTML = get_data.get_main_HTML(base_URL, search_string, vendor)

			if vendor=='flipkart':
				bigBoxes = query_HTML.find_all("a", {"href":re.compile(r"\/.+\/p\/.+qH=.+")})
			elif vendor == 'walmart':
				bigBoxes = query_HTML.find_all('div',{'class':'search-result-gridview-item clearfix arrange-fill'})
			else:
				bigBoxes = query_HTML.find_all("a", {"class": "a-link-normal s-no-outline",
													'href': re.compile(r'\/.+\/dp\/.+?dchild=1.*')})

			product_name_Links = get_data.get_product_name_links(base_URL, bigBoxes)
			for prodName, productLink in product_name_Links[:4]:
				for prod_HTML in get_data.get_prod_HTML(vendor, productLink):
					try:
						prod_price = ''
						if vendor == 'flipkart':
							comment_boxes = prod_HTML.find_all('div', {'class': '_16PBlm'})
							prod_price = prod_HTML.find_all('div', {"class": "_30jeq3 _16Jk6d"})[0].text

						elif vendor == 'walmart':
							comment_boxes = prod_HTML.find_all('div',{'class': 'Grid-col customer-review-body'})
							prod_price = prod_HTML.find('span',{'class':'price-group'}).text
						else:
							comment_boxes = prod_HTML.find_all('div', {'id':re.compile(r'customer_review-.+')})
							try:
								container = prod_HTML.find_all('td', {"class": "a-span12"})
								container = soup(str(container),'html.parser')
								prod_price = container.find_all('span', {"id": "priceblock_ourprice"})[0].text
							except:
								prod_price = prod_HTML.find_all('span', {"class": "a-size-base a-color-price"})[0].text
						if vendor == 'walmart':
							prod_price = float((prod_price.replace("$", "")).replace(",", "").replace(" ",""))
						else:
							prod_price = float((prod_price.replace("₹", "")).replace(",", "").replace(" ",""))
						# print(prod_price)
						for commentbox in comment_boxes:
							get_data.get_final_data(commentbox, prodName, prod_price, vendor)

					except:
						pass
			# save the data as gathered in dataframe
			global df
			df = pd.DataFrame(get_data.get_data_dict())

			# save dataframe as a csv which will be availble to download
			download_path = get_data.save_as_dataframe(df, fileName=search_string.replace("+", "_"))

			# generate and save the wordcloud image
			get_data.save_wordcloud_image(df, 
			img_filename=search_string.replace("+", "_"))

		
			df = DataFrame(get_data.get_data_dict())

			return render_template('review.html',
			tables=[df.to_html(classes='data')],
			titles=df.columns.values,
			search_string = search_string,
			download_csv= '/Users/mohit/TOC-Innovative-Work-Project/static/CSVs'
			)
		except Exception as e:
			print(e)
			return render_template("404.html")

	else:
		return render_template("index.html")

@app.route("/getCSV")
def getCSV():
	global df
	return Response(
		df.to_csv(index = False),
		mimetype="text/csv",
		headers={"Content-disposition":
					 f"attachment;filename=review.csv"})

@app.route('/show')  
@cross_origin()
def show_wordcloud():
	img_file = os.listdir(app.config['IMG_FOLDER'])[0]
	full_filename = os.path.join(app.config['IMG_FOLDER'], img_file)
	return render_template("show_wc.html", user_image = full_filename)


if __name__ == '__main__':
	app.run(debug=True)
