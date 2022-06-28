# sinai_airtable_export
Script to export Airtable data to CSV.

# Using sinai_airtable_export.py

First, make sure you have Python 3 available and [install pipenv](https://pipenv.kennethreitz.org/en/latest/#install-pipenv-today). Then you can use pipenv to install the project's dependencies in a new virtual environment:

```
pipenv install
```

Then, to run commands inside the new virtual environment, you can either enter `pipenv shell` to enter the virtual environment, or you can prefix your commands with `pipenv run`.

You can then use the script to export individual deliveries from Airtable into a CSV for ingest into the Sinai solr index:

```
pipenv run python sinai_airtable_export.py
```

The script will prompt for a delivery number (ex. 4.4) for export. The resulting CSV will save to the airtable_export folder.
