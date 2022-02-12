from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    HttpResponse('<h1>Success</h1>')
