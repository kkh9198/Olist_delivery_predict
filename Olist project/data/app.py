#참고 블로그
#https://niceman.tistory.com/193?category=1009824
#https://aidenlim.dev/19
import time
import json
import os
import ssl
import urllib.request
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3 as sql
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
import getDeliveryTime


app = Flask(__name__)

@app.route('/')
def index():
    con = sql.connect("database.db")
    con.row_factory = sql.Row

    cur = con.cursor()
    
    cur.execute("select distinct CATEGORY from olist_products")

    rows = cur.fetchall()
    return render_template('home.html', rows = rows)    

@app.route('/products/', methods=['POST'])
def searchProducts():
    data = request.form['categoryName']

    con = sql.connect("database.db")
    # con.row_factory=sql.Row
    cur= con.cursor()
    cur.execute("select product_id from olist_products where category = '" + data + "'")
  
    datas = cur.fetchall()
    print(type(datas))
    con.close()

    return jsonify(datas)

# @app.route('/sellers/', methods=['POST'])
# def searchSellers():
#     data = request.form['productId']
#     print("########################"+data)
#     con = sql.connect("database.db")
#     # con.row_factory=sql.Row
#     cur= con.cursor()
#     datas = cur.execute("select seller_id from olist_products where product_id = '" + data + "'").fetchone()
  
#     print(type(datas))
#     print(datas)

#     con.close()

#     return jsonify(datas)

@app.route('/addrec/', methods=['POST', 'GET'])
def addrec():
    if request.method == 'POST':
        #입력값을 받는다.
        customer_lat = request.form['lat']
        customer_lng = request.form['lng']
        product_id = request.form['product_id']

        con = sql.connect("database.db")
        # con.row_factory = sql.Row

        cur = con.cursor()
        
        cur.execute("select * from OLIST_PRODUCTS a LEFT JOIN OLIST_SELLERS b on a.SELLER_ID = b.SELLER_ID where PRODUCT_ID = '" + product_id + "'")

        rows = cur.fetchone()
        product_id= rows[0]
        seller_id= rows[1]
        product_weight_g= rows[2]
        product_volume= rows[3]
        category= rows[4]
        price= rows[5]
        freight_value= rows[6]
        state= rows[8]
        lat= rows[9]
        lng= rows[10]

        
        print(rows)
        print(len(rows))
        print("******************************"+lat + lng)
        #걸리는 시간을 구글에 검색
        origin          = customer_lat+","+customer_lng
        destination     = lat + "," + lng
        mode            = "driving"
        departure_time  = "now"
        key='키값'

        url = "https://maps.googleapis.com/maps/api/directions/json?origin="+ origin \
            + "&destination=" + destination \
            + "&mode=" + mode \
            + "&departure_time=" + departure_time\
            + "&language=ko" \
            + "&key=" + key
        print(url)
        
        request1         = urllib.request.Request(url)
        context         = ssl._create_unverified_context()
        response        = urllib.request.urlopen(request1, context=context)
        responseText    = response.read().decode('utf-8')
        responseJson    = json.loads(responseText)

        with open("./Agent_Transit_Directions.json","w") as rltStream :
            json.dump(responseJson,rltStream)
        #검색 받은 값을 정리
        wholeDict = None
        with open("./Agent_Transit_Directions.json","r") as transitJson :
            wholeDict = dict(json.load(transitJson))
        print(wholeDict)
        path            = wholeDict["routes"][0]["legs"][0]
        duration_sec    = path["distance"]["text"]
        duration_km=duration_sec[0:len(duration_sec)-2]
        #----------------------------------------------
        setdelivery=getDeliveryTime.ss(float(price),float(freight_value),float(product_weight_g),category,state,float(duration_km),float(product_volume))
        model=joblib.load('model.pkl')
        prediction= model.predict(setdelivery)
        print(prediction)
        label=prediction[0]
        result=prediction
        print(result)
        return render_template('result.html', msg=result)

if __name__ == '__main__':
    app.run(debug=True)