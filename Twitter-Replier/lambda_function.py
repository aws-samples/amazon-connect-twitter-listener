# Twitter replier
import tweepy
import boto3
import json
import os
from botocore.exceptions import ClientError

CONNECT_TWITTER_CONFIG = os.environ['CONNECT_TWITTER_CONFIG']



def lambda_handler(event, context):
    print(event)
    STREAM_CONFIG=json.loads(get_config(CONNECT_TWITTER_CONFIG))
    access_token = STREAM_CONFIG['TWITTER_ACCESS_TOKEN']
    access_token_secret = STREAM_CONFIG['TWITTER_ACCESS_TOKEN_SECRET']
    consumer_key = STREAM_CONFIG['TWITTER_CONSUMER_KEY']
    consumer_secret = STREAM_CONFIG['TWITTER_CONSUMER_SECRET']
    
    tweet_id = str(event['Details']['ContactData']['Attributes']['tweet_id'])
    content = str(event['Details']['ContactData']['Description'])
    contactID = str(event['Details']['ContactData']['ContactId'])
    prevcontactID = str(event['Details']['ContactData']['PreviousContactId'])
    instanceARN = str(event['Details']['ContactData']['InstanceARN'])
    instanceID = instanceARN.split(sep='/',maxsplit=2)[1]

    try:
        twitterClient = tweepy.Client(consumer_secret=consumer_secret,consumer_key=consumer_key,access_token=access_token,access_token_secret=access_token_secret)
        twitterClient.create_tweet(in_reply_to_tweet_id=tweet_id,text=content)
        
    except Exception as e:
        print (e)
        return {'MessageSent': False}
    else:
        print(response)
        stop_contact(contactID,instanceID)
        stop_contact(prevcontactID,instanceID)
        return {'MessageSent': True}

def get_config(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            return False
            
def stop_contact(ContactID,InstanceID):
    connect=boto3.client('connect')
    connect.stop_contact(ContactId=ContactID,InstanceId=InstanceID)