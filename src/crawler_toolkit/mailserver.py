import re
import smtplib
from os.path import basename
from crawler_toolkit.share_module import Message
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate


class GMailServer:
    '''Gmail Server

    It is an Mail object which you can structure your mail 
    and send to your target by SMTP mailserver

    :param - account <str>: host to send mail account 
    :param - api_key <str>: SMTP access token api key
    :param - send_to <list|str>: mail receiver
    :param - cc <list|str>: carbon copy receiver
    '''
    def __init__(self, 
            account: str, 
            api_key: str, 
            send_to: list, 
            cc: list=None, 
        ):
        self.account = account
        self.api_key = api_key
        self.send_to = self.mail_prepare(send_to)
        self.cc = self.mail_prepare(cc)
        self.msg = MIMEMultipart()

    @staticmethod
    def mail_prepare(mails :str|list)-> str:
        '''mail_prepare 

        accept str or list mails will prepare object that can send by mailserver
        
        :param - mails <str| list>: passing mail address.
        '''
        if mails:
            if not isinstance(mails, (str, list)):
                raise TypeError('mails only accept type [str| list]')
            if isinstance(mails, str):
                if re.search(',', mails):
                    mails = mails.split(',')
                else:
                    mails = [mails]
        return mails

    def set_mail_info(self, subject: str):
        self.msg['From'] = self.account
        self.msg['To'] = COMMASPACE.join(self.send_to)
        if self.cc:
            self.msg['Cc'] = COMMASPACE.join(self.cc)
        self.msg['Date'] = formatdate(localtime=True)
        self.msg['Subject'] = subject


    def set_html(self, html):
        ''' set html content to mail

        :param - html <str>: html string content to add into mail object
        '''
        self.msg.attach(MIMEText(html, "html"))
    
    def set_text(self, text):
        ''' set text content to mail

        :param - text <str>: string content to add into mail object
        '''
        self.msg.attach(MIMEText(text))

    def set_image(self, filelist_path: list[str]):
        ''' set file img to mail

        :param - filelist_path <list[str]>: set images files to mail from list filepath want to send by mail
        '''
        for filepath in filelist_path:
            with open(filepath, "rb") as f:
                part = MIMEImage(
                    f.read(),
                    Name=basename(filepath)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filepath)
            self.msg.attach(part)

    def set_files(self, filelist_path: list[str]):
        ''' set file obj to mail

        :param - filelist_path <list[str]>: set file to mail from list filepath want to send by mail
        '''
        for filepath in filelist_path:
            with open(filepath, "rb") as f:
                part = MIMEApplication(
                    f.read(),
                    Name=basename(filepath)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filepath)
            self.msg.attach(part)
    
    def send_mail(self, host: str='imap.gmail.com', port: int=465):
        ''' send mail to send_to and cc target mail
        
        :param - host <str>: mail server SMTP_SSL host
        :param - port <int>: mail server SMTP_SSL port
        '''
        Message.splitline('[MailServer]Send Mail', f'from {self.account} To: {self.send_to} CC: {self.cc}')
        with smtplib.SMTP_SSL(host, port) as smtp_server:
            total_send = self.send_to
            if self.cc:
                total_send = total_send + self.cc
            smtp_server.login(self.account, self.api_key)
            smtp_server.sendmail(self.account, total_send, self.msg.as_string())