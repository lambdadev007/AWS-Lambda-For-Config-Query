import json
import boto3

import os
import time
import csv

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.message import Message
from email.encoders import encode_base64
from email.mime.text import MIMEText
from mimetypes import guess_type

# This is the client to access AWS Config
configClient = boto3.client('config')

# This is the client to access AWS SES
sesClient = boto3.client('ses', region_name='us-west-2')

# This is the client to access S3
s3Client = boto3.client('s3')

def json_to_csv(path, objectData, objectName):
    header = []
    for index, data in enumerate(objectData['QueryInfo']['SelectFields']):
        header.append(data['Name'])

    body = []
    for index, data in enumerate(objectData['Results']):
        row = []
        # filteredData = json.dumps(data, indent=4)
        for index, headerItem in enumerate(header):
            headerItemArr = headerItem.split('.')
            columnData = ''
            temp = data
            if(len(headerItemArr) > 1):
                for splitedHeaderItem in headerItemArr: #configuration.state.name
                    try:
                        temp = temp[splitedHeaderItem]
                    except:
                        temp = ''

                columnData = temp
            else:
                columnData = data[headerItem]
            
            row.append(columnData)
        body.append(row)

    with open(os.path.join(path, objectName), 'w', newline='') as fp:
        output = csv.writer(fp)
        output.writerow(header)
        # output.writerow(data['QueryInfo']['SelectFields'])
        for row in body:
            output.writerow(row)

def raw_to_json(raw):
    newResults = []
    for item in raw['Results']:
        jsonItem = json.loads(item)
        newResults.append(jsonItem)
    
    raw['Results'] = newResults

    return raw

def lambda_handler(event, context):

    # Query for the AWS Config discovery
    configResponse = configClient.select_resource_config(
        Expression="SELECT resourceId, resourceType, configuration.instanceType, configuration.placement.tenancy, configuration.imageId, availabilityZone WHERE resourceType = 'AWS::EC2::Instance'"
    )

    # This is the name for the S3 bucket
    s3Bucket = 'config-response-bucket-2'

    # This is the name of the json file
    objectName = 'Results-'+ str(time.time()) +'.csv'

    # This is the python object to hold the results of the query
    objectData = configResponse
    # Try Catch to put object in S3

    jsonData = raw_to_json(objectData)

    json_to_csv('/tmp', jsonData, objectName)

    try:
        s3Client.upload_file('/tmp/' + objectName, Bucket=s3Bucket, Key=objectName)
    except Exception as e:
        print(e)
    else:
        print("Json object has been added to S3")

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "poberezhetspavlo@gmail.com"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    # RECIPIENT = "poberezhetspavlo@gmail.com" #for single recipient
    RECIPIENT = ["poberezhetspavlo@gmail.com", "Mswaroopa@gmail.com"]  #for multiple recipients

    # Subject of the email
    SUBJECT = "AWS Automated Config Delivery"

    # Using the file name, create a new file location for the lambda. This has to
    # be in the tmp dir because that's the only place lambdas let you store up to
    # 500mb of stuff, hence the '/tmp/'+ prefix
    TMP_FILE_NAME = '/tmp/' + objectName

    # Download the file/s from the event (extracted above) to the tmp location
    s3Client.download_file(s3Bucket, objectName, TMP_FILE_NAME)

    # Make explicit that the attachment will have the tmp file path/name. You could just
    # use the TMP_FILE_NAME in the statments below if you'd like.
    ATTACHMENT = TMP_FILE_NAME

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "Hello,\r\nPlease see the attached file related to AWS Config."

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>Please see the attached file related to AWS Config.</p>
    </body>
    </html>
    """

    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECIPIENT)

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(ATTACHMENT, 'rb').read())

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header('Content-Disposition', 'attachment',
                   filename=os.path.basename(ATTACHMENT))

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)

    try:
        # Provide the contents of the email.
        response = sesClient.send_raw_email(
            Source=SENDER,
            Destinations=RECIPIENT,
            RawMessage={
                'Data': msg.as_string(),
            }
        )
    # Display an error if something goes wrong.
    except Exception as e:
        print(e)
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
