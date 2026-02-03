# takes a request => and gives response (a request handler)
# the url in urls.py file in this app is linked to this views.py fuctions
# then you have to import the urls to the urls.py file in main project 

from django.shortcuts import render

def register(request):
    return render(request,'register.html')