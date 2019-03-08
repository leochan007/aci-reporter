#!/usr/bin/python
#coding: utf-8

import os
from pymongo import MongoClient
from bson.son import SON

import pandas as pd
import numpy as np

import xlsxwriter

import smtplib

import traceback
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.application import MIMEApplication

import datetime
import time
import os

import sys

from apscheduler.schedulers.blocking import BlockingScheduler

mongodb_url = 'mongodb://root:example@127.0.0.1:27017/admin?authSource=admin'
table_name = 'credit_inquiry'

db_name = 'alphacar'

config_file = 'config.yaml'

mail_host = 'smtp.exmail.qq.com'
mail_port = 465
sender = 'do-not-reply@alphacar.io'
password = ''
receivers = []

params = dict()

cur_dir = os.path.abspath(os.path.dirname(__file__))

file_name = 'report.xlsx'
output_file = os.path.abspath(os.path.join(cur_dir, file_name))

def loadConfig(configYaml):
    import yaml 
    global mode, mongodb_url, mail_host, mail_port, sender, password, receivers, params
    f = open(configYaml, encoding='utf-8')
    res = yaml.load(f)
    f.close()

    if "MONGODB_URL" in res:
        mongodb_url = res["MONGODB_URL"]

    if "OUTPUT_FILE" in res:
        output_file = res["OUTPUT_FILE"]

    if "MAIL" in res:
        mailInfo = res["MAIL"]
        if "username" in mailInfo:
            sender = mailInfo["username"]
        if "password" in mailInfo:
            password = mailInfo["password"]
        if "to" in mailInfo:
            receivers = mailInfo["to"]

    if "CRON" in res:
        params = res["CRON"]
        tempConf = params['conf']
        s_key = list(tempConf.keys())
        for k_s in s_key:
            if str(tempConf[k_s]).strip() == '':
                del tempConf[k_s]
        params['conf'] = tempConf

    #print(mongodb_url)
    print(output_file)
    print(receivers)

def getData(db_url):
    
    client = MongoClient(db_url)
    db = client[db_name]

    pipeline = [
        {
            '$match': {
                'status': {
                    '$ne': 'deleted'
                }
            }
        },
        {
            '$group': {
                '_id': '$moralCrisisType',
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$sort': {
                'count': 1,
                '_id': 1
            }
        },
    ]

    result = db[table_name].aggregate(pipeline)
    df = pd.DataFrame(columns = ['_id', 'count'])
    for x in result:
        pd_data=pd.DataFrame.from_dict(x,orient='index').T   
        df=df.append(pd_data, ignore_index=True)
    df.index = df['_id']
    return df

def genReport(data, output_file = 'report.xlsx'):
    workbook = xlsxwriter.Workbook(output_file)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': 1})

    headings = ['不诚信记录类型', '人数']

    worksheet.write_row('A1', headings, bold)

    worksheet.write_column('A2', data['_id'])
    worksheet.write_column('B2', data['count'])

    sheetname = 'Sheet1'
    name_line = 1
    data_start_line = 2
    color = 'red'

    max_line = data.shape[0] + data_start_line - 1

    chart_col = workbook.add_chart({'type': 'column'})

    chart_col.add_series({
        'name': '=%s!$B$%d' % (sheetname, name_line),
        'categories': '=%s!$A$%d:$A$%d' % (sheetname, data_start_line, max_line),
        'values':   '=%s!$B$%d:$B$%d' % (sheetname, data_start_line, max_line),
        'line': {'color': color},
    })

    chart_col.set_title({'name': '阿尔法顺风车不诚信人员统计报告'})
    chart_col.set_x_axis({'name': '不诚信记录类型'})
    chart_col.set_y_axis({'name':  '人数'})

    chart_col.set_style(11)

    worksheet.insert_chart('E3', chart_col, {'x_offset': 25, 'y_offset': 10})

    workbook.close()

def sendMail(file_path, date_str):

    global mail_host, mail_port, sender, password, receivers, file_name

    message = MIMEMultipart()

    message['From']=formataddr(["AlphaCar Service", sender])
    message['To']=formataddr(["", ",".join(receivers)])
 
    message['Subject'] = Header('阿尔法顺风车%s诚信报告' % (date_str), 'utf-8')

    message.attach(MIMEText('https://credit.alphacario.com/stats\nAlphaCar社区诚信报告见附件!', 'plain', 'utf-8'))

    xlsxpart = MIMEApplication(open(file_path, 'rb').read())
    xlsxpart.add_header('Content-Disposition', 'attachment', filename=('gbk', '', file_name))
    message.attach(xlsxpart)

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
        #smtpObj.set_debuglevel(True)
        smtpObj.ehlo()
        smtpObj.login(sender, password)
        smtpObj.sendmail(sender, receivers, message.as_string())
        for item in receivers:
            print("item:", item)
        smtpObj.quit()
        print("邮件发送成功")
    except Exception as e:
        print("Error: 无法发送邮件")

def doWork():

    global mongodb_url, output_file

    data = getData(mongodb_url)
    print(data.head())

    genReport(data, output_file)

    cur_date = datetime.datetime.now()
    print('cur_date:', cur_date.strftime('%Y_%m_%d'))

    sendMail(output_file, cur_date.strftime("%Y年%m月%d日"))

def doScheduleWork():
    
    print('params:', params)

    scheduler = BlockingScheduler()
    scheduler.add_job(doWork, params['type'], **params['conf'])

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    scheduler.shutdown()

if __name__ == '__main__':

    if "CONFIG" in os.environ:
        config_file = os.environ["CONFIG"]

    loadConfig(config_file)

    if len(sys.argv) > 1 and sys.argv[1] == 'direct':
        doWork()
    else:
        doScheduleWork()
