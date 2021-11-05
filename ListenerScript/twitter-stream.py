import tweepy
import boto3
import json
from botocore.exceptions import ClientError

REGION = 'ENTER DEPLOYMENT REGION'
CONFIG_SECRET = 'ENTER SECRET NAME CREATED BY DEPLOYMNET'
client = boto3.client(service_name='secretsmanager',region_name=REGION)
try:
  get_secret_value_response = client.get_secret_value(SecretId=CONFIG_SECRET)
except ClientError as e:
  raise e
else:
  STREAM_CONFIG = json.loads(get_secret_value_response['SecretString'])
  print(STREAM_CONFIG)
  access_token = STREAM_CONFIG['TWITTER_ACCESS_TOKEN']
  access_token_secret = STREAM_CONFIG['TWITTER_ACCESS_TOKEN_SECRET']
  consumer_key = STREAM_CONFIG['TWITTER_CONSUMER_KEY']
  consumer_secret = STREAM_CONFIG['TWITTER_CONSUMER_SECRET']
  topic = STREAM_CONFIG['TWITTER_TOPIC']
  kinesis_stream =STREAM_CONFIG['KINESIS_STREAM']
  trackedTopic =[topic]
  kinesis_client = boto3.client('kinesis',region_name=REGION)
  class TwitListener(tweepy.Stream):
    def on_data(self, data):
      parsedData={'tweet_id': json.loads(data)['id'],'text': json.loads(data)['text'],'user_id':json.loads(data)['user']['id'],'name': json.loads(data)['user']['name'],'screen_name': json.loa$
      print(parsedData)
      kinesis_client.put_record(StreamName=kinesis_stream,PartitionKey=topic,Data = json.dumps(parsedData))
      return True
    def on_error(self, status):
      print(status)
  feedStream = TwitListener(consumer_key, consumer_secret,access_token, access_token_secret)
  feedStream.filter(track=trackedTopic)