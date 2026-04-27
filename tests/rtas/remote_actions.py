import wget
import os

def wget_url(base_url, out="."):
    # if not os.path.exists(out):
    #     os.makedirs(out)
    return  wget.download(base_url,
                          #out=out
                          )
    
