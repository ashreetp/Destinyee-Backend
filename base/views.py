from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from pymongo import MongoClient
from bson.json_util import dumps
from django.views.decorators.csrf import csrf_exempt
import bcrypt, json, base64, requests
from .forms import ImageUploadForm
import razorpay


raz_client = razorpay.Client(auth=("rzp_test_fexJOswEsG63La", "gyKjzKdbTbpRUOrLMZaz5v2Z"))

mongo_client = MongoClient("mongodb+srv://destinyee_admin:Destinyeetomoon07@only-cluster.vawhd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db=mongo_client.get_database('destinyee_db')
user_db = db.users
shop_db = db.shop
prod_db = db.products
admin_db = db.admin

# Create your views here.

@csrf_exempt 
def razor(request):
    try:
        caught_data = request.body
        caught_data = json.loads(caught_data)
        order_amount = caught_data['amount']
        order_currency = 'INR'
        order_client = raz_client.order.create({
            "amount": order_amount,
            "currency": order_currency,
        })
        udata = user_db.find_one({'username': caught_data['user']})
        return JsonResponse({"order": order_client, "name": udata['full_name'],"contact":udata['phone_number'], "email": udata['email']})
    except:
        return JsonResponse({"error":"true"})


@csrf_exempt 
def razor_verify(request):
    caught_data = request.body
    caught_data = json.loads(caught_data)
    params_dict = {
        'razorpay_order_id': caught_data['oid'],
        'razorpay_payment_id': caught_data['pid'],
        'razorpay_signature': caught_data['signature']
    }
    try:
        raz_client.utility.verify_payment_signature(params_dict)
        cart_data = user_db.find_one({'username': caught_data['user']})
        user_db.update_one({"username": caught_data['user']},{"$push": {"orders": cart_data['cart'] }})
        user_db.update_one({"username": caught_data['user']},{"$set": {"cart": [] }})
        return JsonResponse({"payment": "Success"})
    except:
        return JsonResponse({"payment": "Fail"})



def home(request):    
    return HttpResponse("Backend working")


#homepage
def shophome(request):
    fin=dumps(shop_db.find())
    fin = json.loads(fin)
    return JsonResponse(fin, safe=False)

def products(request):
    fin=dumps(prod_db.find())
    fin = json.loads(fin)
    return JsonResponse(fin, safe=False)


#User_related
@csrf_exempt 
def user_register(request):
    caught_data = request.body
    caught_data = json.loads(caught_data)
    password = bytes(caught_data['password'],'utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(14))
    caught_data['password'] = hashed
    try:
        if user_db.find_one({"username": caught_data['username']}) == None:
            user_db.insert_one(caught_data)
            return JsonResponse({"inserted":"true"}, safe=False)
        else:
            return JsonResponse({"inserted":"exist"}, safe=False)
    except:
        return JsonResponse({"inserted":"false"}, safe=False)

@csrf_exempt
def user_login(request):
    caught_data = request.body
    caught_data = json.loads(caught_data)
    password = bytes(caught_data['password'],'utf-8')
    try:
        db_data = user_db.find_one({"username": caught_data['username']})
        hashed = db_data['password']
        if bcrypt.checkpw(password, hashed):
            return JsonResponse({"found":"true","token": db_data['token']}, safe=False)
        else:
            return JsonResponse({"found":"false"}, safe=False)
    except:
        return JsonResponse({"found":"error"}, safe=False)

@csrf_exempt
def user_data(request, tname):
    try:
        udata = user_db.find_one({'username': tname})
        return JsonResponse({"cart": udata['cart'],"orders": udata['orders']}, safe=False)
    except:
        return JsonResponse({"Error": "true"}, safe=False) 

@csrf_exempt
def user_update_cart(request):
    try:
        caught_data = request.body
        caught_data = json.loads(caught_data)
        user_db.update_one({"username":caught_data['username']},{'$push': {'cart': caught_data['cart']}})
        return JsonResponse({"update_cart": "true"}, safe=False)
    except:
        return JsonResponse({"Error": "true"}, safe=False)

@csrf_exempt
def user_remove_cart_item(request):
    try:
        caught_data = request.body
        caught_data = json.loads(caught_data)
        user_db.update( {"username" : caught_data['username']} , {'$pull' : {"cart" : {"prod_id": caught_data['prod_id']}} } , False , True)
        return JsonResponse({"deleted_cart": "true"}, safe=False)
    except:
        return JsonResponse({"Error": "true"}, safe=False)

@csrf_exempt
def user_change_data(request):
    try:
        caught_data = request.body
        caught_data = json.loads(caught_data)
        found = user_db.find_one({"username": caught_data['username']})
        if(caught_data['type'] == 'ch_pass'):
            if bcrypt.checkpw(bytes(caught_data['cur_pass'],'utf-8'), found['password']):
                hashed = bcrypt.hashpw(bytes(caught_data['new_pass'],'utf-8'), bcrypt.gensalt(14))
                user_db.update_one({"username": caught_data['username']},{"$set":{"password": hashed}})
        elif caught_data['type'] == 'ch_phno':
            user_db.update_one({"username": caught_data['username']},{"$set":{"phone_number": caught_data['new_phno']}})
        elif caught_data['type'] == 'ch_email':
            user_db.update_one({"username": caught_data['username']},{"$set":{"email": caught_data['new_email']}})
        elif caught_data['type'] == 'ch_add':
            user_db.update_one({"username": caught_data['username']},{"$set":{"address": caught_data['new_add']}})
        elif caught_data['type'] == 'del':
            user_db.remove_one({"username": caught_data['username']})
        return JsonResponse({"deleted_cart": "true"}, safe=False)
    except:
        return JsonResponse({"Error": "true"}, safe=False)


#Admin related
@csrf_exempt
def admin_upload_product(request):
    caught_data = request.body
    caught_data = json.loads(caught_data)
    size={}
    csize=caught_data['size']
    csize=list(csize.split(','))
    for item in csize:
        item=item.split('=')
        size[item[0]]=int(item[1])
    cdesc=caught_data['description']
    cdesc=list(cdesc.split('\n\n'))
    cdesc_inner=[]
    for item in cdesc:
        cdesc_inner.append(item.split('\n'))
    caught_data['description']=cdesc_inner
    caught_data['size']=size
    caught_data['img']=""
    caught_data['gallary']=[]
    prod_db.insert_one(caught_data)
    return JsonResponse({"uploaded":"true"})

@csrf_exempt
def admin_login(request):
    caught_data = request.body
    caught_data = json.loads(caught_data)
    password = caught_data['password']
    try:
        db_data = admin_db.find_one({"username": caught_data['username']})
        db_password = db_data['password']
        if db_password == password:
            return JsonResponse({"admin_login":"true"}, safe=False)
        else:
            return JsonResponse({"admin_login":"false"}, safe=False)
    except:
        return JsonResponse({"admin_login":"false"}, safe=False)

def handle_uploaded_file(f): 
    with open('static/img.jpg', 'wb+') as destination:  
        for chunk in f.chunks():  
            destination.write(chunk)

def handle_imgbb_upload():
    apiKey = '688cb8d79477a95a2a1f0a3355cb84ee'
    fileLocation = "static/img.jpg"
    with open(fileLocation, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": apiKey,
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)
        fin = json.loads(res.content)
        return fin['data']['url']

@csrf_exempt
def send_img(request):
    if len(request.FILES) == 1:
        prod_id = str(request.FILES['image'])
        prod_id=prod_id.split('.')[0][:-1]
        handle_uploaded_file(request.FILES['image'])
        imgbb_url = handle_imgbb_upload()
        prod_db.update_one({"prod_id": prod_id},{"$set": {"img": imgbb_url}})
        prod_db.update_one({"prod_id": prod_id},{"$push": {"gallary": imgbb_url}})
    else:
        for i in range(len(request.FILES)):
            prod_id = str(request.FILES[str(i)])
            prod_id=prod_id.split('.')[0][:-1]
            handle_uploaded_file(request.FILES[str(i)])
            imgbb_url = handle_imgbb_upload()
            prod_db.update_one({"prod_id": prod_id},{"$push": {"gallary": imgbb_url}})
    return JsonResponse({"image_upload":"true"})
        
