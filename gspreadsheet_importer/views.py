from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.db import connection 
from django.db.models import get_model, get_apps
from django.conf import settings
import gdata.spreadsheet.service
import gdata.service
import atom.service
import gdata.spreadsheet
import atom
from gspreadsheet_importer.spreadsheet import *
from django.contrib.auth.decorators import login_required

def authenticate(request):
  gd_client = request.session.get('gd_client')
   
  if gd_client: 
    return gd_client
  elif request.GET.has_key('token'):
    url = "http://%s%s" % (request.get_host(), request.get_full_path())
    token = gdata.auth.extract_auth_sub_token_from_url(url)
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.UpgradeToSessionToken(token)
    request.session['gd_client'] = gd_client
    return gd_client

  return None

def get_authsuburl(request):
  next = "http://%s%s" % (request.get_host(), request.path)
  scope = 'https://spreadsheets.google.com/feeds/'
  secure = False
  session = True

  if 'GOOGLE_SPREADSHEET_DOMAIN' in settings.get_all_members():
     domain = settings.GOOGLE_SPREADSHEET_DOMAIN
  else:
    domain = "default"
   
  gd_client = gdata.spreadsheet.service.SpreadsheetsService()
  return gd_client.GenerateAuthSubURL(next, scope, secure=secure, session=session, domain=domain)

def get_spreadsheets(gd_client):
  return [entry.title.text for i, entry in enumerate(gd_client.GetSpreadsheetsFeed().entry)]

@login_required
def index(request):  
  gd_client = authenticate(request)
  
  ctx = Context({})
  if gd_client:
    ctx['spreadsheets'] = get_spreadsheets(gd_client)
    ctx['app'] = request.path.split('/')[2]
  else:
    ctx['authsub_url'] = get_authsuburl(request)
    
  return render_to_response('gspreadsheet_importer/index.html', context_instance=ctx)

def load_data(request):
  gd_client = authenticate(request)
  
  app_name = request.path.split('/')[2]
  delete_existing_data = request.GET.has_key('delete_existing_data')
  si = SpreadsheetImporter()
  results = si.import_spreadsheet(gd_client, request.GET['spreadsheet'], app_name, delete_existing_data)
  
  ctx = Context({})
  ctx['spreadsheet'] =  request.GET['spreadsheet'] 
  ctx['app'] = app_name
  ctx['results'] = results
  ctx['spreadsheets'] = get_spreadsheets(gd_client)
    
  return render_to_response('gspreadsheet_importer/index.html', context_instance=ctx)
