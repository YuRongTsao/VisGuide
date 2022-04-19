import datetime, time
import os, platform
import json
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select

from calendar import monthrange

#BeautifulSoup
from bs4 import BeautifulSoup
import re

keys = ['city','station','year','month','day','weekday']
week = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
dataArray = []
formerStation = ''
currentStation = ''
dataObject = {}

year = '2018'
wfilePath = '..\\day_value\\' + year + '\\csv\\'
fileName = '空氣品質監測日值'+year+'-'
fileType = '.json'
missFilePath = 'missRecord.txt'

f = open(missFilePath, "a")

def parseData(browser):
	soup = BeautifulSoup(browser.page_source, 'html.parser')
	table = soup.find("table",{"class":"tbResult gvColspan"})
	rows = table.find_all('tr')
	global currentStation,formerStation,dataArray,dataObject

	for rindex,row in enumerate(rows): 
		if rindex >= 4 and rindex<=len(rows)-3:
			cols = row.find_all('td')
			currentStation = cols[2].text.strip() 
			materialObject = {}
			materialArray = []
			materialKey = ''
			isPass = 0

			for item in dataArray:
				try:
					if item["station"] == currentStation:
						isPass = 1
				except:
					check = 1 
			if(isPass!=1):
				if formerStation == '' or currentStation!=formerStation:
					#print(dataObject)
					dataArray.append(dataObject)
					dataObject = {} 

				for index,col in enumerate(cols):
					value = col.text.strip()	
					if index == 0:
						dataObject[keys[0]] = value
					elif index == 2:
						dataObject[keys[1]] = value
					elif index == 3:
						date = value
						date = date.split("/")
						if date:
							dataObject[keys[2]] = date[0]
							dataObject[keys[3]] = date[1]
							dataObject[keys[4]] = date[2]
							dataObject[keys[5]] = week[datetime.date(int(date[0]), int(date[1]),int(date[2])).weekday()]
					elif index == 4:
						materialKey = value
						materialKey = materialKey.replace("\n","")
					elif index!=1:
						materialArray.append(value)
				for index,hourValue in enumerate(materialArray):
					if index < 10:
						hour = '0'+str(index)
					else:
						hour = str(index)
					materialObject[hour] = hourValue
			
				dataObject[materialKey] = materialObject
				formerStation = currentStation
	

def writeFile(dataArray,month,day):
	with open(wfilePath+fileName+month+day+fileType, 'w',encoding='utf-8') as hour_value:
		json.dump(dataArray, hour_value, ensure_ascii=False)
	

chrome_options = webdriver.ChromeOptions()
# Disable Notifications
chrome_options.add_experimental_option("prefs",{"profile.default_content_setting_values.notifications" : 2})
# Maximize Window size 
chrome_options.add_argument("-start-maximized")

browser = webdriver.Chrome(executable_path="chromedriver.exe",chrome_options=chrome_options)


########## keep the Observer's account and password in "Observer.txt"
########## To avoid DNS recording again

########## Login website ##########
browser.get("https://erdb.epa.gov.tw/DataRepository/EnvMonitor/AirQualityMonitorDayData.aspx?utm_source=erdb.epa.gov.tw&utm_medium=ERDBIndex")
### Successfully login
print("Successfully Login .")

select = Select( browser.find_element_by_name("ctl00$ContentPlaceHolder1$ucSearchCondition$ddlYearE") )
select.select_by_value(year)
browser.execute_script("arguments[0].click()", browser.find_element_by_name("ctl00$ContentPlaceHolder1$imgSearch") )


# 選 月/日期搭配
for month in range(12):
	monthRange = monthrange(int(year),month+1)[1]
	if month+1<10:
		month_s = '0'+str(month+1)
	else:
		month_s = str(month+1)

	select = Select( browser.find_element_by_name("ctl00$ContentPlaceHolder1$ucSearchCondition$ddlMonthE") )
	select.select_by_value(month_s)
	#確認查詢
	browser.execute_script("arguments[0].click()", browser.find_element_by_name("ctl00$ContentPlaceHolder1$imgSearch") )

	#for day in range(16):
	for day in range(monthRange):
		if day+1<10:
			day_s = '0'+str(day+1)
		else:
			day_s = str(day+1)

		selectDay = Select( browser.find_element_by_name("ctl00$ContentPlaceHolder1$ucSearchCondition$ddlDayE") )
		selectDay.select_by_value(day_s)
		browser.execute_script("arguments[0].click()", browser.find_element_by_name("ctl00$ContentPlaceHolder1$imgSearch") )
		
#抓取表格內容和換頁
		try:
			isPass = 1
			table = browser.find_element_by_class_name("gv_pager_style")
			for pageID in range(11):
				try:
					tablePage = browser.find_element_by_class_name("gv_pager_style").find_elements_by_tag_name("td")
					tablePage[pageID+1].click()
					if (pageID+1) != 11:
						parseData(browser)
					sleep(2)
				except:
					print(month_s+'/'+day_s+' page < 10')
					f.write(month_s+'/'+day_s+' page < 10\n')
					isPass = 0
					break
			nofirst=1
			if isPass == 1:
				for pageID in range(11):
					try:
						tablePage = browser.find_element_by_class_name("gv_pager_style").find_elements_by_tag_name("td")
						tablePage[pageID+1+nofirst].click()
						if (pageID+1) != 11:
							parseData(browser)
						sleep(2)
					except :
						print(month_s+'/'+day_s+' page < 20')
						f.write(month_s+'/'+day_s+' page < 20\n')
						isPass = 0
						break
				nofirst = 5
			if isPass == 1:
				for pageID in range(6):
					try:
						tablePage = browser.find_element_by_class_name("gv_pager_style").find_elements_by_tag_name("td")
						tablePage[pageID+1+nofirst].click()
						parseData(browser)
						sleep(2)
					except:
						print(month_s+'/'+day_s+' page < 26')
						f.write(month_s+'/'+day_s+' page < 26\n')
						break

			dataArray.append(dataObject)
			writeFile(dataArray,month_s,day_s)
			dataArray =[]
			dataObject = {} 
        		
		except:
        		print(month_s+'/'+day_s+' no result')
        		f.write(month_s+'/'+day_s+' no result\n')
				
# end crawler
browser.quit()