
Install development environment
===============================


Open up Terminal and do the following

1. Set up your virtualenv

    ~> virtualenv -p python2.6 --no-site-packages haruka
    ~/haruka> source bin/activate

2. Clone Repository

    ~/haruka> git clone git@github.com:catalpainternational/HarukaSMS.git

3. Install dependencies 

    ~/haruka> cd HarukaSMS
    ~/haruka/HarukaSMS> pip install -r requirements.txt

4. Create the database

    ~/haruka/HarukaSMS> python manage.py syncdb

5. Run the development webserver
 
	~/haruka/HarukaSMS> python manage.py runserver

