import schedule
from datetime import datetime,timedelta
import os
import time

PATH = 'apt-insight/assets/data/' # 데이터 저장 경로
filepath = os.path.join(PATH, 'text.txt')

def job():
    date = datetime.now().strftime('%Y%m%d_%H%M%S')
    f = open(filepath, 'a')
    f.write('hello world' + date)
    f.close()

schedule.every(3).seconds.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)    