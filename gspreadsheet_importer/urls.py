from django.conf.urls.defaults import *

urlpatterns = patterns('',
        (r'^import$', 'gspreadsheet_importer.views.index'),
        (r'^loaddata$', 'gspreadsheet_importer.views.load_data')
)
