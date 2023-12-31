import requests
from flask import Flask, request, render_template, redirect
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, decode_token,get_jwt_identity
import bcrypt
from database import connect_to_db, init_db
import database, os, json

# INIT the Flask APP
app = Flask(__name__)


'''
JWT INITIALIZATION
'''
# INIT JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Replace with a secure secret key
jwt = JWTManager(app)


'''
DATABASE INITIALIZATION
'''
# Connect To DB
conn = connect_to_db()

# DB Initializing Route
@app.route("/initdb")
def initdb():
    msg=init_db(conn)
    return msg


'''
PAGE ROUTE FUNCTIONS FOR SHOP
'''
# Shop Login Page Route
@app.route("/shop/login")
def shopLogin():
    return render_template('shop/login.html')

# Shop Home Page Route
@app.route("/shop")
def shop():
    return render_template('shop/shop.html')

# Shop Orders Page Route
@app.route("/shop/orders")
def shopOrders():
    # Request to get the list of orders
    response = requests.get("http://127.0.0.1:"+os.getenv('APP_PORT')+"/api/shop/getOrderList")
    if response.status_code == 200:
        # Return the orderlist as list with 200 status
        orderlist=response.json()['data']
        return render_template('shop/orders.html', orderlist=orderlist), 200
    else:
        return render_template('shop/orders.html'), 422

# Shop Order ID Page Route
@app.route("/shop/order/<orderid>")
def shopOrderPage(orderid):
    # Request to get the order for that order id
    response = requests.get("http://127.0.0.1:"+os.getenv('APP_PORT')+"/api/shop/getOrder/"+orderid)
    if response.status_code == 200:
        # Return the order as dict
        order=response.json()['data']
        return render_template('shop/orderpage.html', order=order), 200
    else:
        return render_template('shop/orderpage.html'), 422

'''
PAGE ROUTE FUNCTIONS FOR CUSTOMER
'''
# Home Page Route
@app.route("/")
def home():
    return render_template('customer/homepage.html')

# Login Page Route
@app.route("/login")
def login():
    return render_template('customer/login.html')

# Sign-Up Page Route
@app.route("/signup")
def signup():
    return render_template('customer/signup.html')

# Search Page Route
@app.route("/search/<key>")
def searchPage(key):
    response=searchHelper(key)
    if(response["res"]==1):
        return render_template('customer/search.html', medicines=response["data"])
    return render_template('customer/search.html')

# Medicine Page Route
@app.route("/medicine/<id>")
def medicinePage(id):
    response=medicineDetails(id)
    if(response["res"]==1):
        return render_template('customer/medicine_page.html', medicine=response["data"])
    return render_template('customer/medicine_page.html')

# Account Page Route
@app.route("/myaccount/<accessToken>")
def myAccountPage(accessToken):
    # Add AccessToken as header
    headers = {
    'Authorization': f'Bearer {accessToken}'
    }
    # Request to get all the orders for that user
    response = requests.get("http://127.0.0.1:"+os.getenv('APP_PORT')+"/api/getOrderList", headers=headers)
    if response.status_code == 200:
        # Return page with orderlist and username
        orderlist=response.json()['data']
        username=response.json()['username']
        return render_template('customer/myaccount.html', username=username, orderlist=orderlist), 200
    else:
        return render_template('customer/myaccount.html'), 422

# Order Page Route
@app.route("/myorder/<accessToken>/<id>")
def myOrderPage(accessToken,id):
    # Add AccessToken as header
    headers = {
    'Authorization': f'Bearer {accessToken}'
    }
    # Request to get the orders for the orderid
    response = requests.get("http://127.0.0.1:"+os.getenv('APP_PORT')+"/api/getOrder/"+id, headers=headers)
    if response.status_code == 200:
        # Return the order as dict
        order=response.json()['data']
        return render_template('customer/orderpage.html', order=order), 200
    else:
        return render_template('customer/orderpage.html'), 422

# Create Order Page Route
@app.route("/createOrder")
def createOrderPage():
    return render_template('customer/create_order.html'), 200 

# Cart Page Route
@app.route("/cart")
def cartPage():
    return render_template('customer/cart.html'), 200 

'''
API FUNCTIONS BELOW FOR CUSTOMER
'''
# Signup API
@app.post("/api/signup")
def signupHelper():
    data = request.get_json()

    # Get the username and password from post
    username=data["username"]
    password=data["password"]

    # Hash Password with bcrypt library
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Store user details in customerAuth table
    data = {
            'username': username,
            'password': hashed_password.decode('utf-8')
        }
    response=database.insert(conn=conn, table="customerAuth", data=data)
    print(response)

    # Return the response
    if response["res"]==1:
        return {"res": 1, "message": "Sign Up Successful"}
    else:
        return {"res": 0, "message": "Sign Up Unsuccessful! User Already Exists"}
    
# Login API
@app.post("/api/login")
def loginHelper():
    data = request.get_json()

    # Get the credentials
    username=data["username"]
    password=data["password"]

    # Search in database if user exists
    response=database.select(conn=conn, table="customerAuth", condition=f"username='{username}'")
    
    print(response)

    # If search successful
    if(response["res"]==1 and len(response["result"])!=0):
        # Get the hashed db password
        hashed_password=response["result"][0][1]
        
        # Check if its same with input credentials
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            # Prepare a JWT token
            access_token = create_access_token(identity=username)
            
            # DELETE THIS LINE
            # print(access_token)

            # Return the accesstoken (JWT) for that user
            return {"res": 1, "message": "User Logged In", "accessToken": access_token}
        else:
            return {"res": 0, "message": "Incorrect Password"}
    else:
        return {"res": 0, "message": "User Does Not Exist"}
    
# Logout API
@app.get("/api/logout")
@jwt_required()
def logoutHelper():
    # Get user details from accesstoken
    current_user = decode_token(request.headers['Authorization'][7:])  # Extract the token from the "Bearer" header
    username = current_user['sub']

    # Check if user exists
    response=database.select(conn=conn, table="customerAuth", condition=f"username='{username}'")
    response["result"]=response["result"][0]
    print(response)

    # If search successful
    if(response["res"]==1):
        return {"res": 1, "message": "Logged Out Successfully"}
    else:
        return {"res": 0, "message": "Error Logging Out"}

# Check Log In
@app.get("/api/isvalid")
@jwt_required()
def isValid():
    # Get user details from accesstoken
    current_user = decode_token(request.headers['Authorization'][7:])  # Extract the token from the "Bearer" header
    username = current_user['sub']

    # Check if user exists
    response=database.select(conn=conn, table="customerAuth", condition=f"username='{username}'")
    response["result"]=response["result"][0]
    print(response)

    # If search successful
    if(response["res"]==1):
        return {"res": 1, "message": "User is Valid"}
    else:
        return {"res": 0, "message": "User Invalid"}

# Search Medicine API
@app.get("/api/search/<key>")
def searchHelper(key):
    # Search using the key in medicine table
    response=database.select(conn,"medicines", columns=["id","name","composition","price"], condition=f"name ILIKE '%{key}%' OR composition ILIKE '%{key}%'", limit=20)
    if(response["res"]==0):
        return {"res": 0, "message": "Search Failure"}
    
    # Get the matched medicine with the key
    searchedMedicine=[]
    for med in response["result"]:
        data={
            "id":med[0],
            "name":med[1],
            "composition":med[2],
            "price":med[3],
        }
        searchedMedicine.append(data)
    
    # Return the result
    return {"res": 1, "message": "Search Success", "data": searchedMedicine}

# Get medicine details API
@app.get("/api/medicine/<id>")
def medicineDetails(id):
    # Get the medicine with that id
    response=database.select(conn,"medicines", condition=f"id='{id}'")
    if(response["res"]==0):
        return {"res": 0, "message": "Get Medicine Details Failure"}
    
    # Prepare a JSON/dict before sending
    data={
            "id":response["result"][0][0],
            "name":response["result"][0][1],
            "composition":response["result"][0][2],
            "price":response["result"][0][3],
            "manufacturer":response["result"][0][4],
            "description":response["result"][0][5],
            "category":response["result"][0][6],
            "side_effects":response["result"][0][7],
        }

    # Return the response
    return {"res": 1, "message": "Medicine Details Fetched", "data": data}

# Create Order API
@app.post("/api/createOrder")
@jwt_required()
def createOrder():
    # Get the user details from accesstoken
    current_user = decode_token(request.headers['Authorization'][7:])  # Extract the token from the "Bearer" header
    username = current_user['sub']

    # Get the order details from post body
    data = request.get_json()

    # Calculate the total amount
    response=calculateTotal(data["cart"])
    if(response['res']==0):
        return response
    
    # Insert the order in DB
    total=response['total']
    print(total)
    data["time"]="CURRENT_TIMESTAMP(2)"
    data["cart"]=json.dumps(data["cart"])
    data["status"]="Order Received"
    query = f'''INSERT INTO orders 
    (username,time,name,address,contact,cart,status,total) VALUES (
    '{username}',{data["time"]},'{data["name"]}','{data["address"]}',
    '{data["contact"]}', '{data["cart"]}', '{data["status"]}',{total})'''
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return {"res": 1, "message": "Insertion Success"}
    except Exception as e:
        print(e)
        return {"res": 0, "message": "Insertion Failure"}

# Get Order API
@app.get("/api/getOrder/<orderid>")
@jwt_required()
def getOrder(orderid):
    # Get the user details from accesstoken
    current_user = decode_token(request.headers['Authorization'][7:])  # Extract the token from the "Bearer" header
    username = current_user['sub']

    # Search for that order id
    response=database.select(conn,"orders",condition=f"orderid={orderid} AND username='{username}'")
    
    # Prepare a JSON/dict before sending
    if(response["res"]==1):
        result=response["result"][0]
        data={
            "orderid": result[0],
            "username": result[1],
            "time": result[2],
            "name": result[3],
            "address": result[4],
            "contact": result[5],
            "cart": json.loads(result[6]),
            "status": result[7],
            "total": result[8]
        }
        return {"res": 1, "message": "Order Fetched", "data": data}
    return {"res": 0, "message": "Order Could Not be Fetched"}

# Get Order List API
@app.get("/api/getOrderList")
@jwt_required()
def getOrderList():
    # Get the user details from accesstoken
    current_user = decode_token(request.headers['Authorization'][7:])  # Extract the token from the "Bearer" header
    username = current_user['sub']
    print(username)

    # Search for orders for that user
    response=database.select(conn,"orders", columns=["orderid","time","total","status"], condition=f"username='{username}'")
    print(response)

    # return the response
    if(response["res"]==1):
        return {"res": 1, "message": "Order List Fetched", "username":username, "data": response["result"]}
    return {"res": 0, "message": "Order Could Not be Fetched"}

# Get the cart total
@app.post("/api/getCartTotal")
def getCartTotal():
    data = request.get_json()
    cart=data["cart"]
    return calculateTotal(cart)

'''
API FUNCTIONS BELOW FOR SHOP
'''
# Shop Login API
@app.post("/api/shop/login")
def shopLoginHelper():
    data = request.get_json()

    # Get the credentials
    username=data["username"]
    password=data["password"]

    # Check if it matches
    if(username=="admin" and password=="admin"):
        return {"res": 1, "message": "Admin Logged In"}
    return {"res": 0, "message": "Admin Login Failure"}

# Shop Order List API
@app.get("/api/shop/getOrderList")
def shopGetOrderList():
    # Get the orders from db
    response=database.select(conn, table="orders", columns=["orderid","username","time","total","status"])
    print(response)
    # Return the response
    if(response["res"]==1):
        return {"res": 1, "message": "Order List Fetched", "data": response["result"]}
    return {"res": 0, "message": "Order Could Not be Fetched"}

# Shop Get Order API
@app.get("/api/shop/getOrder/<orderid>")
def shopGetOrder(orderid):
    # Get the order based on order id
    response=database.select(conn,"orders",condition=f"orderid={orderid}")
    
    # Return the response
    if(response["res"]==1):
        result=response["result"][0]
        data={
            "orderid": result[0],
            "username": result[1],
            "time": result[2],
            "name": result[3],
            "address": result[4],
            "contact": result[5],
            "cart": json.loads(result[6]),
            "status": result[7],
            "total": result[8]
        }
        return {"res": 1, "message": "Order Fetched", "data": data}
    return {"res": 0, "message": "Order Could Not be Fetched"}

# Shop Update Order API
@app.post("/api/shop/updateOrder")
def shopUpdateOrder():
    data = request.get_json()

    print(data)

    # Get the credentials
    orderid=data["orderid"]
    status=data["status"]

    # Update the status of that orderid
    response=database.update(conn,"orders",{"status":status},condition=f"orderid={orderid}")
    print(response)
    if response["res"]==1:
        return {"res": 1, "message": "Update Successful"}
    else:
        return {"res": 0, "message": "Update Unsuccessful!"}
    
'''
NORMAL FUNCTIONS
'''
# Calculates the total amount based on cart using DB
def calculateTotal(cart):
    total=0
    for item in cart:
        response=database.select(conn, table="medicines", columns=["price"], condition=f"id={item['id']}")
        if(response['res']==0):
            return {"res": 0, "message": "Selection Failure", "total": total}
        total+=float(response["result"][0][0][1:])*int(item['qty'])
    total=round(total,2)
    return {"res": 1, "message": "Selection Success", "total": total}
'''
MAIN FUNCTION
'''
if __name__ == '__main__':
    # Run the Flask app
    print(initdb())
    app.run(debug=True, use_reloader=True, port=os.getenv('APP_PORT'))
