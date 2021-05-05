import requests


def saveImageFromURL(url: str, dest: str):
    request = requests.get(url,stream=True)
    with open(dest,mode='wb') as f:
        f.write(request.content)

def splitGIFIntoImages(gifPath: str, frameMarking='I'): #in format e.g. frame-I, frame-II, should also work with integers if 1 is passed
    pass