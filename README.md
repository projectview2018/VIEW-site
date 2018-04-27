VIEW is a blind spot calculator made to enable purchases to make more informed decision which take direct vision into account, it is used as part of the panoramic method. Drivers have a significantly faster reaction time to direct vision versus vision through mirrors or screens. It also allows vulnerable road users like pedestrians and bicyclists to make eye contact with the driver which is useful for their navigation of traffic. These vulnerable road users made up 16% of all traffic fatalities in 2016.

Find more on this topic and the panoramic method [here](TODO).

You can find this site at [https://blindspotcalculator.herokuapp.com/](https://blindspotcalculator.herokuapp.com/).

______________________

To run this site on your own Heroku instance follow the [Heroku’s instructions](https://devcenter.heroku.com/articles/getting-started-with-python#introduction) but using this repository instead of Heroku's python-getting-started app.

To summarize this document you must have:
A Heroku account - it’s free
Python 3.6 installed locally
Pipenv installed locally
Postgres installed locally, if running the app locally

Next, login to heroku in your shell using the command: 
```console
$ heroku login
```
Then run:
```console
$ git clone https://github.com/LucyWilcox/VIEW-site.git
$ cd VIEW-site
$ heroku create
$ git push heroku master
$ heroku open
```
This will create and open a Heroku site which will allow you to enter information about a vehicle and determine the scale of its blindspots.

To keep a database of trucks you have scanned, you will need to provision a database, you can do this following steps in [Heroku’s documentation in the “Provision a Database” step](https://devcenter.heroku.com/articles/getting-started-with-python#introduction).

Critically you must run:
```console
$ heroku run python manage.py migrate
```
You should now be able to add trucks and view trucks you have saved in your database by adding a VIN number.
