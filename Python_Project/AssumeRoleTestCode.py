aws configure 

import boto3

client = boto3.client('sts')

cred = client.assume_role(RoleArn='arn:aws:iam::29YourID8350:role/stsassumeroleforkinesis', RoleSessionName= 'Molex', ExternalId='VeryUniqueID1')

kinclient = boto3.client('kinesis',aws_access_key_id=cred['Credentials']['AccessKeyId'], aws_secret_access_key=cred['Credentials']['SecretAccessKey'],aws_session_token=cred['Credentials']['SessionToken'])

response = kinclient.list_shards( StreamName='freezer_data')

print (response)


