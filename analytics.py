from flask import Flask, render_template
import requests
from flask import request


app = Flask(__name__)

url = "https://zotmeal-backend.vercel.app/api/"
#url = "http://localhost:3000/api/"

@app.route('/', methods=["GET", "POST"])
def home():
	return render_template('home.html')

@app.route('/analytics')
def analytics():
	print("here")
	url2 = url + "?analytics=test"
	resp = requests.get(url=url2)
	data = resp.json()
	return render_template('analytics.html', count=data["visitcount"], error=data["errorcount"])

@app.route('/meal', methods=["GET", "POST"])
def meal():
	location, date, meal = request.form["location"], request.form["date"], request.form["meal"]
	modified_datestring = date.replace("/","|")
	url2 = url + "?location=" + location+"&date="+modified_datestring+"&meal="+meal
	resp = requests.get(url=url2)
	data = resp.json()
		
	return data