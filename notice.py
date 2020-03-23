#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2020-03-13                                                         #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""

import sys
sys.path.append(".")
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from base import ScoutBase, Loger


class PyEmail(ScoutBase):
    sender = ''     #发送者
    
    """
    @name: 构造函数
    @desc: 读取配置文件,初始化变量
    """
    def __init__(self):
        ScoutBase.__init__(self)

        if not self.avr['admin_email'].find('@'):
            self.sender = self.avr['smtp_server'].replace(self.avr['smtp_server'].split('.')[0]+'.',self.avr['admin_email']+'@')
        else:
            self.sender = self.avr['admin_email']  
        

    """
    @name: 普通发信模式
    @desc: 不需要SSl认证
    """
    def nonsend(self,subject, msg, receiver):
        msg = MIMEText(msg,'plain','utf-8') #中文需参数‘utf-8’，单字节字符不需要
        msg['Subject'] = subject
        smtp = smtplib.SMTP()
        smtp.connect(self.avr['smtp_server'])
        smtp.login(self.avr['smtp_user'], self.avr['smtp_passwd'])
        smtp.sendmail(self.sender, receiver, msg.as_string())
        smtp.quit()
        
    """
    @name: SSL发信模式
    @desc: 支持google邮箱
    """
    def sslsend(self,subject, msg, receiver):
        msg = MIMEText(msg,'plain','utf-8') #中文需参数‘utf-8’，单字节字符不需要
        msg['Subject'] = Header(subject, 'utf-8')
        smtp = smtplib.SMTP()
        smtp.connect(self.avr['smtp_server'])
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.set_debuglevel(1)
        smtp.login(self.avr['smtp_user'], self.avr['smtp_passwd'])
        smtp.sendmail(self.sender, receiver, msg.as_string())
        smtp.quit()
        
    """
    @name: 发送邮件
    """    
    def sendto(self,subject, msg, receiver):
        if self.avr['smtp_ssl']:
            try:
                self.sslsend(subject, msg, receiver)
                Loger().WARNING('[MAIL] Send mail Success.')
            except Exception as e:
                Loger().ERROR('[MAIL] Send mail failed to: %s' % e)
        else:
            try:
                self.nonsend(subject, msg, receiver)
                Loger().WARNING('[MAIL] Send mail Success.')
            except Exception as e:
                Loger().ERROR('[MAIL] Send mail failed to: %s' % e)
    
