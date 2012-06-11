
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

4. Make sure your HUAWEI dongle is plugged into your USB port

5. Start a new Terminal Session. (This is to ensure that step 6 works)

6. Create the database

    	~/haruka/HarukaSMS> python manage.py syncdb

7. Run the development webserver
 
		~/haruka/HarukaSMS> python manage.py runserver &

8. Run the GSM router
		
		~/haruka/HarukaSMS> pygsm-gateway.py
