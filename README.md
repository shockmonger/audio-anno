Audio Annotation tool for Hindustani music
------------------------------------------

## Install
* Figure out how to install pip (the python package manager) in your distro and
install it
> `<your-package-manager> install python-dev python-pip`
* Install `virtualenv`
> `sudo pip install virtualenv`
* Create a virtual environment in the current folder
> `virtualenv venv`
* Activate the virtual environment
> `source venv/bin/activate`
* Install dependencies for the application
> `python setup.py install`

## Configure
* Create a `config.py` from the sample config
> `cp sample_config.py config.py`
* Edit values in `config.py` and put appropriate values

## Run
* `python server.py`
