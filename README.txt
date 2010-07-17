gspreadsheet-importer is a utility to access a private Google Spreadsheet and suck the data into a Django data model. OneToOne and ManyToMany fields are supported. The app includes an admin console that can be integrated into your target application's interface. Here's how it works:

* Setup your Google spreadsheet
> Each worksheet represents an individual model. The worksheet name is your model name
> If relationships exist, worksheets are ordered in their dependency order, most abstract objects first
> The first row in the worksheet is the header row. Each column should have a model attribute name.  
-- If a model attribute represents a OneToOneField or ManyToManyField, the column name should include the foreign key type separated by a period, e.g. my model attribute Author is of type Person. The column name should be Author.Person. The code will automatically pick up a type if the model attribute happens to be the same as the referenced object, e.g. my model attribute is Person. The column name can simply be Person.
> When entering data for foreign key fields, the program assumes objects have an attribute named "name". This field is used to lookup or create the related object.
> DateTimeField format: %m/%d/%Y %H:%M:%S
> DateField format: %m/%d/%Y

* Add the project to your installed_apps.

* If not using the default gmail.com domain, specify the hosted domain in settings_shared.py. e.g. GOOGLE_SPREADSHEET_DOMAIN = 'my.hosted.domain.com'

* In your urls.py, add the following line BEFORE any admin includes. The application will pick up the app name from the url.
(r'^admin/<appname>/', include('gspreadsheet_importer.urls'))

* Run the application and login to your admin console. Navigate to http://<coolcompany.com>/admin/<appname>/import

* The app uses AuthSub authentication to login and access Google data. The admin interface will guide you through these steps.

* Choose a spreadsheet and hit Import.

* Success/error messaging is displayed.
