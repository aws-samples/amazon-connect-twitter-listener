#Twitter Stream Processor
import base64
import json
import boto3
import os
from botocore.exceptions import ClientError

CONNECT_TWITTER_CONFIG = os.environ['CONNECT_TWITTER_CONFIG']

def queueTweets(event, context):
    STREAM_CONFIG=json.loads(get_config(CONNECT_TWITTER_CONFIG))
    INSTANCE_ID = STREAM_CONFIG['CONNECT_INSTANCE_ID']
    CONTACT_FLOW_ID= STREAM_CONFIG['CONTACT_FLOW_ID']
    client = boto3.client('comprehend')
    output = []
    for record in event['Records']:
        tweet = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8').strip())
        language = client.detect_dominant_language(Text=tweet['text'])
        score_language = 0
        dominant_language='en'
        for lang in language['Languages']:
            if (lang['Score']>=score_language):
                dominant_language = lang['LanguageCode']
                score_language = lang['Score']
                print('lang:'+dominant_language + " - score:" + str(score_language))
        print(dominant_language)
        sentiment = client.detect_sentiment(Text=tweet['text'], LanguageCode=dominant_language)

        tweet = {
            'tweet_id': str(tweet['tweet_id']),
            'user_id': str(tweet['user_id']),
            'text': str(tweet['text']),
            'name': tweet['name'],
            'user_name':tweet['screen_name'],
            'sentiment': sentiment['Sentiment'],
            'language': dominant_language,
            #'recordId': record['kinesis']['sequenceNumber']
        }
        print(tweet)
        start_task(tweet,INSTANCE_ID,CONTACT_FLOW_ID)
        output.append(tweet)
    
    return {'Tweets': output}


def start_task(tweet_attributes,INSTANCE_ID,CONTACT_FLOW_ID):
    connect_client = boto3.client("connect")

    response = connect_client.start_task_contact(
    InstanceId=INSTANCE_ID,
    ContactFlowId=CONTACT_FLOW_ID,
    Attributes=tweet_attributes,
    Name='@'+str(tweet_attributes['user_name']),
    Description= tweet_attributes['text']
    )
    
    print(response)

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
