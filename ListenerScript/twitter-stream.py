import tweepy
import boto3
import json
import time
from botocore.exceptions import ClientError
REGION="us-west-2"
client = boto3.client(service_name='secretsmanager',region_name=REGION)
logGroup='TwitterStreamer'

try:
  get_secret_value_response = client.get_secret_value(SecretId="arn:aws:secretsmanager:us-west-2:758580162203:secret:ConnectTwitterConfig-VKaqUf")
except ClientError as e:
  raise e
else:
  STREAM_CONFIG = json.loads(get_secret_value_response['SecretString'])
  access_token = STREAM_CONFIG['TWITTER_ACCESS_TOKEN']
  access_token_secret = STREAM_CONFIG['TWITTER_ACCESS_TOKEN_SECRET']
  consumer_key = STREAM_CONFIG['TWITTER_CONSUMER_KEY']
  consumer_secret = STREAM_CONFIG['TWITTER_CONSUMER_SECRET']
  topic = STREAM_CONFIG['TWITTER_TOPIC']
  kinesis_stream =STREAM_CONFIG['KINESIS_STREAM']
  trackedTopic =[topic]
  kinesis_client = boto3.client('kinesis',region_name=REGION)
  cw_logs = boto3.client('logs',region_name=REGION)
  try:
    cw_logs.create_log_group(logGroupName=logGroup)
  except ClientError as e:
    print(e)
  logStream = 'Stream'+str(int(time.time()*1000))
  try:
    print(cw_logs.create_log_stream(logGroupName=logGroup,logStreamName=logStream))
  except ClientError as e:
    raise e
  else:
    cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': 'Starting'}])

  class TwitListener(tweepy.Stream):
    def on_data(self, data):
      print('Received data:' + str(data))
      parsedData={'tweet_id': json.loads(data)['id'],'text': json.loads(data)['text'],'user_id':json.loads(data)['user']['id'],'name': json.loads(data)['user']['name'],'screen_$
      print(parsedData)
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      print(logs)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      print(logsToken)
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': json.dumps(parsedData)}],sequ$
      kinesis_client.put_record(StreamName=kinesis_stream,PartitionKey=topic,Data = json.dumps(parsedData))
      print('Waiting')
      time.sleep(10)
      return True

    def on_error(self, status):
      print('Error received:' + str(status))
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': status}],sequenceToken=logsTo$
      print('Waiting')
      time.sleep(60)
      return True

    def on_limit(track):
      print(track)
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': track}],sequenceToken=logsTok$
      print('Waiting')
      time.sleep(60)
      return True
    def on_disconnect_message(message):
      print(message)
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': message}],sequenceToken=logsT$
      return True

  feedStream = TwitListener(consumer_key, consumer_secret,access_token, access_token_secret)
  feedStream.filter(track=trackedTopic, stall_warnings='true')