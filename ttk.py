from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import urlopen
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import time
import lxml
import datetime
import re
import sys
import pymysql

ReParticipantsUrl = re.compile('"url_token": "(.*?)", "id"')
Url = "https://www.zhihu.com/lives/814564305038082048"
#Url = "https://www.zhihu.com/lives/890607769521115136"
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'}
s = requests.Session()

_xsrf='30d4a23b-6557-4fc8-9ff9-f943ea4995bd'

loginurl = 'https://www.zhihu.com/login/email'
formdata={
  'email':'lzy19970509@qq.com',
  'password':'qq1997lzy0509',
  '_xsrf':'_xsrf'
  
  }
z5 = s.post(url=loginurl,data=formdata,headers=headers)
mylog='https://www.zhihu.com/people/lin-yang-72-83/logs'
s.get(url=mylog)


driver = webdriver.Firefox()

initUrl = "http://www.zhihu.com"
driver.get(initUrl)
wait=WebDriverWait(driver,100)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "GlobalSideBar-categoryList")))
driver.get(initUrl)

conn =pymysql.connect(host='localhost',user='root',password='qq1997lzy0509',port=3306,db='zhihu',use_unicode=True,charset="utf8")
cursor=conn.cursor()
def GetInfo(path):
    list0 = []
    with open(path,"r") as f:
        for i in re.split('\n',f.read()):
           list0.append( str(i))
    return list0

def SaveTemp(list1,path):
     list0 = GetInfo(path)
    
     with open (path,"a") as f:
        for i in list1:
            if i not in list0:
                f.write(i+"\n")
            else:
                continue
     return      

    
def GetFansIdList(LiveOwnerId): #传入live举办者的url 返回关注live主的人的url列表
    Url ="https://www.zhihu.com/people/"+ LiveOwnerId+"/followers"
    driver.get(Url)
    path = "E://Fans.txt"
    
    time.sleep(1)
    
    peopleId =str(driver.current_url)[29:-10]
    
    Bs = BeautifulSoup(driver.page_source, 'lxml')
    FansNum = Bs.findAll("strong", {"NumberBoard-itemValue"})[1].attrs["title"]
    

    a = int(int(FansNum) / 20)

    FansIdList = []

    for i in range(a + 1):
        FansPageUrl = "https://www.zhihu.com/people/"+ peopleId+"/followers" + "?page=" + str(i + 1)
        driver.get(FansPageUrl)
        time.sleep(1)

        FansPageBs = BeautifulSoup(driver.page_source, 'lxml')

        People = FansPageBs.findAll("a", {"class": "UserLink-link"})
        for y in People:
            FansId = str(re.split("/", str(y.attrs['href']))[-1])
            
            if FansId not in FansIdList:
                FansIdList.append(FansId)
                
        time.sleep(0.03)
    SaveTemp(FansIdList,path)
    return path


def GetLiveParticipantsIdList(LiveId, ParticipantsNum): #传入liveId live 参加人数 返回参加live所有人的URL

    a = int(int(ParticipantsNum) / 3000)
    path ="E://participants.txt"
    ParticipantsIdList = []

    for i in range(a):
        ParticipantsUrl = "https://api.zhihu.com/lives/" + LiveId + "/members?limit=" + str((i + 1) * 3000) + "&offset=" + str(i * 3000)
        html = urlopen(ParticipantsUrl)

        ParticipantsBs = BeautifulSoup(html.read(), 'lxml')

        IdList = re.split("}, {", ParticipantsBs.find("p").get_text())

        for i in IdList:
            if len(ReParticipantsUrl.findall(i)) > 0:
                Url =  ReParticipantsUrl.findall(i)[0]
                ParticipantsIdList.append(Url)

    ParticipantsUrl = "https://api.zhihu.com/lives/" + LiveId + "/members?limit=" + ParticipantsNum + "&offset=" + str(a * 3000)
    html = urlopen(ParticipantsUrl)

    ParticipantsBs = BeautifulSoup(html.read(), 'lxml')

    IdList = re.split("}, {", ParticipantsBs.find("p").get_text())

    for i in IdList:
        if len(ReParticipantsUrl.findall(i)) > 0:
            Url = ReParticipantsUrl.findall(i)[0]
            ParticipantsIdList.append(Url)
    SaveTemp(ParticipantsIdList,path)
    return path

def GetLiveINI(Url): #方法传入参数为知乎Live Url
    sqlLive ="insert into Live (liveId,liveName,organizerId,sTime,score,numOfReview,numOfMember,numOfAudio,numOfFile,numOfAnswer)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    sqlJoinLive ="insert into JoinLive (liveId,peopleId) values(%s,%s)"
    sqlFollow ="insert into Follow (peopleId,followingId) values(%s,%s)"

    driver.get(Url)
    time.sleep(1)
    PageSource = driver.page_source

    bs = BeautifulSoup(PageSource, 'lxml')

    LiveId = Url[-18:]
    try:

        Name = bs.find("div", {"class": "LivePageHeader-line-SzR2 LivePageHeader-title-1RQL"}).string#Live名字
    except:
        Name =""
    date = bs.find("div", {"class": "LivePageHeader-timeNumber-3dX8"}).get_text()
    Year = int(str(date)[:4])
    Month = int(str(date)[5:7])
    Day = int(str(date)[8:10])

    Date = datetime.datetime(Year, Month, Day)#Live举办时间

    Star = bs.find("span", {"class": "LiveContentInfo-scoreNum-Qa-K"}).get_text()#Live星级数

    EvaluationNum = int(str(bs.find("div", {"class": "LiveContentInfo-reviewText-1ncS"}).get_text())[:-9])#Live评论数

    INFList = bs.findAll("div", {"class": "LiveContentInfo-item-w7BI"})

    mid =""
    for i in INFList:
        mid=mid+str(i)
    
    try:
        Aswer = str(re.search("问答",mid).group())
        
    except:
        Aswer = ""
    try:
        File = str(re.search("文件",mid).group())
        
    except:
        File =""

    SoundMinute = int(INFList[0].findAll("div")[0].get_text()) #Live分钟语音数
    
    if Aswer == "问答" :
        AswerNum = int(INFList[1].findAll("div")[0].get_text()) #Live文件数
        if File == "文件":
            FileNum = int(INFList[2].findAll("div")[0].get_text())
        else:
            FileNum = 0
        
    else:
        AswerNum =0
        if File == "文件":
            FileNum = int(INFList[1].findAll("div")[0].get_text())
        else:
            FileNum = 0

    LiveParticipantsNum = str(bs.find("span", {"class": "Participants-text--jB3"}).get_text())[:-5]

    #LiveOwnerId =  str(bs.find("a", {"class": "LiveSpeakers-link-6dN8 UserLink-root-1ogW"})['href'])[13:] #Live举办人个人信息主页ID
  

    #LiveOwnerId= GetPeople(LiveOwnerId)
    LiveOwnerId = "wpox"

    
    try:

        cursor.execute(sqlLive,(LiveId,Name,LiveOwnerId,Date,Star,str(EvaluationNum),str(LiveParticipantsNum),str(SoundMinute),str(FileNum),str(AswerNum)))
        conn.commit()
    except:
        print("liveId:"+LiveId)

    
    #ParticipantsPath = GetLiveParticipantsIdList(LiveId, LiveParticipantsNum) #Live听众的Id

    #FansPath = GetFansIdList(LiveOwnerId) #关注Live主的用户的Id
        
    #ParticipantsPath = "E://participants.txt"
    FansPath = "E://Fans.txt"
    FansIdList = GetInfo(FansPath)
    #ParticipantsIdList = GetInfo(ParticipantsPath)


    #for i in ParticipantsIdList:
     #   if i != "":            
      #      try:
       #         GetPeople(i)
        #    except:
         #       pass
          #  try:
           #     cursor.execute(sqlJoinLive,(LiveId,i))
           #     conn.commit()
            #except:
             #   print("participantId:"+i)

   
    for i in FansIdList:
        
        
        if i != "" :
            
            try:
                GetPeople(i)
            except:
                pass
            try:
                cursor.execute(sqlFollow,(LiveOwnerId,i))
                conn.commit()
            except:
                print("fanId:"+i)
            
                
    GetReview(LiveId,EvaluationNum)
    
def GetQuestion(peopleId,Num):
    sql ="insert into Question (questionId,questionName,qTime,qPeople,numOfFollow,numOfAnswer)values(%s,%s,%s,%s,%s,%s)"
    peopleUrl="https://www.zhihu.com/people/" + peopleId + "/asks"
    a = int(int(Num)/20)
    for i in range(a+1):
        questionUrl = peopleUrl + "?page="+str(i+1)
        driver.get(questionUrl)
        time.sleep(1)

        askbs = BeautifulSoup(driver.page_source, 'lxml')
        askList = askbs.findAll("div",{"class":"List-item"})
        for j in askList:
            mid= j.find("a",{"data-za-detail-view-name":"Title"}).attrs["href"]
            name=j.find("a",{"data-za-detail-view-name":"Title"}).string
            href = re.search("\d+$",str(mid)).group()
            detail = j.findAll("span",{"class":"ContentItem-statusItem"})
            askdate = detail[0].string
            Year = int(str(askdate)[:4])
            Month = int(str(askdate)[5:7])
            Day = int(str(askdate)[8:10])

            Date = datetime.datetime(Year, Month, Day)
            numOfAnswer =int(re.search("\d*", detail[1].string).group())
            numOfFocus =int(re.search("\d*",detail[2].string).group())
            
            try:
                cursor.execute(sql,(href,name,Date,peopleId,str(numOfFocus),str(numOfAnswer)))
                conn.commit()
            except:
                pass
            
        
    
def GetAnswer(peopleId,Num):
    sql = "insert into Answer (answerId,question,numOfAgree,numOfReview,aTime,aPeople) values (%s,%s,%s,%s,%s,%s)"
    peopleUrl ="https://www.zhihu.com/people/"+ peopleId + "/answers"
    a = int(int(Num)/20)
    for i in range(a+1):
        answerPageUrl = peopleUrl + "?page="+str(i+1)
        driver.get(answerPageUrl)
        time.sleep(1)

        answerPagebs = BeautifulSoup(driver.page_source, 'lxml')
        answerList = answerPagebs.findAll("div",{"class":"List-item"})
      
        for j in answerList:
            mid=str(j.find("a",{"data-za-detail-view-element_name":"Title"}).attrs["href"])
            aquestion=re.sub("/","",str(re.search("/\d+/",mid).group()))
            answerId =re.sub("/answer/","",str(re.search("/answer/\d+",mid).group()))
            answerUrl = "https://www.zhihu.com" + mid
            try:
                up = j.find("button",{"aria-label":"赞同"}).get_text()
            except:
                up = 0
            try:
                
                html0 = s.get(answerUrl,headers=headers)
                answerbs = BeautifulSoup(html0.text, 'lxml').find("div",{"class":"QuestionAnswer-content"})
            except:
                driver.get(answerUrl)
                answerbs = BeautifulSoup(driver.page_source, 'lxml').find("div",{"class":"QuestionAnswer-content"})
            
            try:
                if up == "0":
                   numOfAgree = 0
                else:
                   numOfAgree = int(re.search("\d*",str(answerbs.find("button",{"class","Button Button--plain"}).get_text())).group())
            except:
                numOfAgree = 0


            try:
                try:
                    mid = re.search("发布于 昨天" ,str(answerbs.find("div",{"class":"ContentItem-time"}))).group()
                except:
                    mid =re.search("发布于 \d+-\d+-\d+" ,str(answerbs.find("div",{"class":"ContentItem-time"}))).group()
            except:
                print(answerbs)
                continue
           

            contentTime = re.sub("(发布于| )","",str(mid))
            

            if str(contentTime)[:4] == '昨天':
                Year = 2018
                Month = 2
                Day = 6
            else:
                Year = int(str(contentTime)[:4])
                Month = int(str(contentTime)[5:7])
                Day = int(str(contentTime)[8:10])
        
            Date = datetime.datetime(Year, Month, Day)
            try:
                
                mid =str(answerbs.findAll("div",{"class":"ContentItem-actions"})[0])
                numOfReview=int(re.sub("( |条评论)","",str(re.search("\d 条评论",mid).group())))
            except:
                numOfReview =0
                
            try:
                cursor.execute(sql,(answerId,aquestion,str(numOfAgree),str(numOfReview),Date,peopleId))
                conn.commit()
            except:
                pass

            
def GetPeople(peopleId):
    peopleUrl ="https://www.zhihu.com/people/"+ peopleId
    sql="insert into People(peopleId,peopleName,numOfQuestion,numOfAnswer,numOfFollowing,numOfFollowed,numOfAgree,numOfThanks,numOfcollected,numOfShareEditing,numOfArticle)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    driver.get(peopleUrl)
    time.sleep(1)
    peopleId =re.split("/",str(driver.current_url))[-2]
    page = driver.page_source
    bs = BeautifulSoup(page,"lxml")
    peopleName =bs.find("span",{"class":"ProfileHeader-name"}).string
    follow = bs.findAll("strong", {"class":"NumberBoard-itemValue"})
    numOfFollowing = int(follow[0].attrs["title"])
    numOfFollowed = int(follow[1].attrs["title"])
    numOfAnswer = int(re.sub(",","",bs.find("li",{"aria-controls":"Profile-answers"}).span.string))
    numOfAsk = int(re.sub(",","",bs.find("li",{"aria-controls":"Profile-asks"}).span.string))
    numOfArticle = int(re.sub(",","",bs.find("li",{"aria-controls":"Profile-posts"}).span.string))
    
    card = bs.find("div",{"class":"Profile-sideColumn"})
    
    try:
        mid= re.search(">[\d,]+<",str(re.search("获得.*?次赞同",str(card)).group())).group()
        
        numOfAgree=int(re.sub("(<|>|,)","",mid))
    except:
        numOfAgree = 0
    
        
    try:
        mid=re.search("获得 \d.*?\d 次感谢",str(card)).group()
        
        numOfThanks =int(re.sub("(获得|,|次感谢)","",mid))     
    except:
        numOfThanks = 0
       
    try:
        mid =re.split(">",re.search(">.*?次收藏",str(card)).group())[-1]
        
        numOfCollected =int(re.sub("(>|,|次收藏)","",mid))
    except:
        numOfCollected = 0
       
    try:
        mid = re.search(">[\d,]+<",str(re.search("参与.*?次公共编辑",str(card)).group())).group()
        
        numOfShareEditing =int(re.sub("(,|>|<)","",mid))
    except:
        numOfShareEditing = 0
   
    try:
        cursor.execute(sql,(peopleId,peopleName,str(numOfAsk),str(numOfAnswer),str(numOfFollowing),str(numOfFollowed),str(numOfAgree),str(numOfThanks),str(numOfCollected),str(numOfShareEditing),str(numOfArticle)))
        conn.commit()
    except:
        print("people:"+ peopleId)
        
    GetQuestion(peopleId,numOfAsk)
    GetAnswer(peopleId,numOfAnswer)

    return peopleId
    
def GetReview(liveId,Num):
    sql ="insert into LiveReview(liveId,peopleId,liveReview,reply,reviewStar,reviewDate) values (%s,%s,%s,%s,%s,%s)"
    
    Url ="https://www.zhihu.com/lives" + liveId + "/reviews"
    driver.get(Url)
    time.sleep(1)
    Comment=[]
  
    while(len(Comment)<int(Num)):
        non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
        driver.execute_script("window.scrollBy(0,5000)")
        PageSource = driver.page_source

        bs = BeautifulSoup(PageSource, 'lxml')
        Comment = bs.findAll("div",{"data-za-module":"CommentItem"})
        
    for i in Comment:
       UserName = i.find("img",{"class":"Avatar-image-uu3z"}).attrs["alt"]
       try:
           UserId = str(i.find("a",{"class":"UserLink-root-1ogW"}).attrs["href"])[-32:]
           peopleUrl ="https://www.zhihu.com/people/"+ UserId
           driver.get(peopleUrl)
           time.sleep(0.05)
           UserId =str(driver.current_url)[29:-11]
           
       except:
           UserId ="00000000000000000000000000000000"
       UserCommentStar = re.search("[1-5]",str(i.find("div",{"class":""}).attrs['aria-label'])).group()
       try:
           UserComment = str(i.find("div",{"class":"ReviewItem-text-22Wg"}).string).translate(non_bmp_map)
           
       except:
           UserComment =""
       try:
           Reply = i.find("div",{"class":"ReviewItem-reply-1_lH"}).get_text()
       except:
           Reply =""
       try:
           CommentDate =re.sub("编辑于","",i.find("div",{"class":"ReviewItem-date-2XBc"}).find("span").string)
           Year = int(str(CommentDate)[:4])
           Month = int(str(CommentDate)[5:7])
           Day = int(str(CommentDate)[8:10])

           Date = datetime.datetime(Year, Month, Day)
       except:
           pass
       try:
           cursor.execute(sql,(liveId,UserId,UserComment,Reply,UserCommentStar,Date))
           conn.commit()
       except:
           pass
          








GetLiveINI(Url)
conn.close()
driver.close()

