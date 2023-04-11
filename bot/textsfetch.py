import requests
import yaml

def getset():
    with open("texts.yaml", 'r') as f:
        data = yaml.safe_load(f)
    return data
