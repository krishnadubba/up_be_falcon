# UGGIPUGGI  
Built with Python, and more specifically with Falcon framework and MongoEngine (python client for MongoDB).

To get started, please follow instructions below on how to setup your environment to run uggipuggi


## Instructions

> #### Prerequisites for Local Environment
> Uggipuggi assumes a MongoDB data store for persistence. Make sure you have [MongoDB installed](https://www.mongodb.org/downloads) and a running instance for Uggipuggi to connect to. 
>
> You may change the settings in the [dev.ini file in config directory].

We first need to install all the dependencies or packages needed (a virtualenv is recommended).

```
$ python setup.py develop
```

## Up and Running

Before running the application, we need to have our database up. Do `$sudo mongod`.
Assuming you are already in the project directory, simply run the following command:

```
$ gunicorn -b 0.0.0.0:8000 manage:uggipuggi.app
```

Point your browser to localhost:8000/recipes (thereby making a GET request).
Try adding params in your URL, for instance, http://localhost:8000/recipes?title=egg_curry&tags=breakfast

To try a POST request, you can do the following via the Terminal:

```
$ curl -X  POST -H "Content-Type:application/json" -d '[PAYLOAD HERE]' http://localhost:8000/recipes
```

If you wish to see the response in prettyprint, you can pipe the response with Python's json module: `| python -m json.tool`

Of course, you may prefer to use POSTMAN.io (easy GUI) to make these POST request. That is fine too.
Do note that Uggipuggi only accepts json [content-type](http://en.wikipedia.org/wiki/Internet_media_type) for POST requests.

## Testing & Contributing

Before pushing codes, please ensure that the code is checked against flake8 firstly

```
$ python setup.py flake8
```

Next, to check tests and coverage reports:

1. Ensure MongoDB is running on your local machine. To start MongoDB: `$ sudo mongod`

2. Run the tests by doing: `$ coverage run setup.py nosetests`

Let's try to keep the code clean with Flake8, and less bug-free with testing!
Target coverage: 80% (current: 100%)

## Deploying

When deploying to environments other than your local environment ('dev'), please ensure that you set the 'UGGIPUGGI_BACKEND_ENV' environment variable in the OS before running the server.
This is so that the right config file can be loaded for initializing the application.

## API methods

A list of API methods can be found [here](endpoints.md)

