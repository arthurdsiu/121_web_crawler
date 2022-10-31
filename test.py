import re
from urllib.parse import urlparse
from scraper import isBadDomain
from scraper import is_valid
s1 = "http://www.ics.uci.edu/~eppstein/pix/sdcbcw/1.html"
s2 = "http://www.economics.uci.edu/people/officehours.php"
s3 = "google.com.php/asdf"
s4 = "http://www.ics.uci.edu/~eppstein"
#parsed = url.urlparse(s1)
#if re.search('pix', parsed.path):
#    print("yes")
'''

print(isBadDomain(urlparse(s1).hostname ))
print(urlparse(s2).hostname)
print(isBadDomain( urlparse(s2).hostname))
print(isBadDomain (urlparse(s3).hostname))
'''
print(is_valid(s1))
print(is_valid(s2))
print(is_valid(s3))
print(is_valid(s4))