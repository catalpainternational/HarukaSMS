
Install development environment
-------------------------------


Open up Terminal and do the following

1. Set up your virtualenv

		~> virtualenv -p --no-site-packages haruka
		~/haruka> source bin/activate

2. Clone Repository

    	~/haruka> git clone git@github.com:catalpainternational/HarukaSMS.git

3. Install dependencies 

    	~/haruka> cd HarukaSMS
    	~/haruka/HarukaSMS> pip install -r requirements.txt

4. Start a new Terminal Session. (This is to ensure that step 6 works)

4. Create the database

    	~/haruka/HarukaSMS> python manage.py syncdb

5. Run the development webserver
 
		~/haruka/HarukaSMS> python manage.py runserver &

6. Run the GSM router
		
		~/haruka/HarukaSMS> pygsm-gateway.py
