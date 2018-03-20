
from bs4 import BeautifulSoup
from selenium import webdriver
import lxml
import time
import re
import sys

sys.setrecursionlimit(1000000)
path0 = "E://dataChack.txt"
url_list = set()
url=""
with open(path0,'r')as f:
    for i in re.split('\n',f.read()):
      url_list.add( str(i))


urllist0 = set()
for i in url_list:
   urllist0.add(i)


driver=webdriver.Firefox()





def gethtml(Url):
    
        
    driver.get(Url)

    try:
            time.sleep(2)
            driver.find_element_by_class_name('LiveRelatedLives-viewMore-ebUQ').click()
    except:
            time.sleep(1)
    for i in range(20):
           driver.execute_script("window.scrollBy(0,5000)")
           time.sleep(1)
       
    pageSource = driver.page_source
    bs = BeautifulSoup(pageSource, 'lxml')
    list = bs.findAll("a", {"data-za-module": "LiveItem"})
    
    for i in list:
        URL = "https://www.zhihu.com" + i['href']
        if (URL not in url_list):
            url_list.add(URL)
            with open (path0,'a')as f:
                 f.write(URL + '\n')
            print(len(url_list))
            
          
            gethtml(URL)
        else:
            continue
 
   


def main():
    k = 0
    for i in urllist0:
      try:
       gethtml(i)
      except:
        print("error"+ str(k))
        
        continue
      k=k+1
      
   

main()


print(len(url_list))
