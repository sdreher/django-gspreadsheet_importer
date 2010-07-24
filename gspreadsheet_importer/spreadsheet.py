import gdata.spreadsheet.service
import gdata.service
import gdata.spreadsheet
import datetime, sys, time
from django.db.models import get_model, get_app, get_models, ForeignKey, OneToOneField, ManyToManyField, DateTimeField, DateField

class SpreadsheetColumn:
  attribute_name = None
  column_type = None
  value = None
  
  def get_type_name(self):
    if self.column_type:
      return self.column_type
    else:
      return self.attribute_name
  
  def get_entry_name(self):
    if self.column_type:
      return '%s.%s' % (self.attribute_name, self.column_type)
    else:
      return self.attribute_name

class SpreadsheetImporter:
  
  results = {} # map of object name + count of objects imported
  
  def import_spreadsheet(self, gd_client, spreadsheet_name, app_name, delete_existing_data=False):
    if delete_existing_data:
      self._prepare_database(app_name)
      
    spreadsheet_feed = gd_client.GetSpreadsheetsFeed()
    for i, entry in enumerate(spreadsheet_feed.entry):
      if entry.title.text == spreadsheet_name:
        
        id_parts = entry.id.text.split('/')
        key = id_parts[len(id_parts) - 1]
        feed = gd_client.GetWorksheetsFeed(key)
    
        for i, entry in enumerate(feed.entry):
          id_parts = entry.id.text.split('/')
          worksheetId = id_parts[len(id_parts) - 1]
          model = get_model(app_name, entry.title.text)
          self.results[model._meta.verbose_name] = {'count': 0, 'errors': [] }   
          
          feed = gd_client.GetListFeed(key, worksheetId)
      
          for i, entry in enumerate(feed.entry):
            self._process_model_object(gd_client, entry, model, app_name)
              
            
    return self.results

  def _prepare_database(self, app_name):
    module = get_app(app_name)
    models = get_models(module) # Assumes models are listed in dependency order -- todo: anyway to do this without hard-coding?
    models.reverse()
    for m in models:
      m.objects.all().delete() 

  def _parse_columns(self, map):
    columns = {}
    
    for k,v in map.items():
      c = SpreadsheetColumn()
      c.value = v.text
      a = k.split('.')
      if len(a) > 0:
        c.attribute_name = a[0]
        c.column_type = a[0]
      if len(a) > 1:
        c.column_type = a[1]

      columns[c.attribute_name] = c
      
    return columns

  def _process_model_object(self, gd_client, entry, model, app_name):  
    attributes = {} # for error messaging
    try:
      opts = model._meta
      obj = model() # bare model instance
      columns = self._parse_columns(entry.custom) # list of columns, indexed by the model attribute name.
      
      # iterate the regular fields, these include everything but many_to_many
      for field in opts.fields:
        attribute_name = field.name.strip().replace('_', '') # google spreadsheets strips spaces and underscores
        
        if attribute_name in columns.keys():
          column = columns[attribute_name]
          value = column.value
          
          if value != None:
            attributes[field.name] = 'Error'

            if isinstance(field, ForeignKey) or isinstance(field, OneToOneField):
              related_model = get_model(app_name, column.get_type_name())
              value, created = related_model.objects.get_or_create(name=value)
            elif isinstance(field, DateTimeField):
              t = time.strptime(value, '%m/%d/%Y %H:%M:%S')
              value = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
            elif isinstance(field, DateField):
              t = time.strptime(value, '%m/%d/%Y')
              value = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
            
            obj.__setattr__(field.name, value)
            attributes[field.name] = str(value)
                  
      obj.save()
      
      # set the many_to_many fields after the save
      # prior to the save, the object has no primary key,
      # so django is unable to do the lookup in the related many-to-many table
      for field in opts.many_to_many:
        related_model_name = field.name.strip().replace('_', '')
        if related_model_name in columns.keys():
          column = columns[related_model_name]
          if column.value != None:
            attributes[field.name] = 'Error'
            related_model = get_model(app_name, column.get_type_name())
            values = column.value.split(',')
            for v in column.value.split(','):
              related_obj, created = related_model.objects.get_or_create(name=v.strip()) 
              obj.__getattribute__(field.name).add(related_obj)
              attributes[field.name] = v.strip()

      obj.save()
      self.results[model._meta.verbose_name]['count'] += 1
    except:
      error = {}
      error['attributes'] = attributes
      error['error_message'] = sys.exc_info()
      self.results[model._meta.verbose_name]['errors'].append(error)
      

    
