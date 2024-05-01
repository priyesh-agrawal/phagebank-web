def send_email_without_attachment(receiver_address, mail_subject, mail_text):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    smtp_port = 587  # For starttls
    smtp_server = "smtp.office365.com"
    sender_email = "phagebank@aphage.com"
    receiver_email = receiver_address
    password = ""

    msg = MIMEMultipart()

    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = mail_subject

    body = mail_text

    msg.attach(MIMEText(body, 'html'))

    receiver_email_list = receiver_email.split(",")

    #print('receiver_email_list', receiver_email_list)
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        server_log = server.set_debuglevel(2)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email_list, msg.as_string())

        server.quit()

        return 'success'
    except Exception as Err:
        return 'Error {}'.format(str(Err))
