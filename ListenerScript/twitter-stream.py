mport tweepy
import boto3
import json
import time
from botocore.exceptions import ClientError
REGION="REGION-IDENTIFIER"
client = boto3.client(service_name='secretsmanager',region_name=REGION)
logGroup='/aws/ec2/twitter-listener'
try:
  get_secret_value_response = client.get_secret_value(SecretId="SECRET-ARN")
except ClientError as e:
  raise e
else:
  STREAM_CONFIG = json.loads(get_secret_value_response['SecretString'])
  BEARER_TOKEN = STREAM_CONFIG['TWITTER_BEARER_TOKEN']
  topic = STREAM_CONFIG['TWITTER_TOPIC']
  kinesis_stream =STREAM_CONFIG['KINESIS_STREAM']
  kinesis_client = boto3.client('kinesis',region_name=REGION)
  cw_logs = boto3.client('logs',region_name=REGION)
  try:
    cw_logs.create_log_group(logGroupName=logGroup)
  except ClientError as e:
    print('Error creating CW Log group')
    print(e)
  logStream = 'Stream'+str(int(time.time()*1000))
  try:
      print(cw_logs.create_log_stream(logGroupName=logGroup,logStreamName=logStream))
  except ClientError as e:
    print('Error creating CW Log stream')
  else:
    cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': 'Starting'}])
  class TwitListener(tweepy.StreamingClient):
    def on_data(self, data):
      jsonData = json.loads(data)
      parsedData={'tweet_id': jsonData['data']['id'],'text': jsonData['data']['text'],'lang':jsonData['data']['lang'],'user_id':jsonData['data']['author_id']}
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': json.dumps(parsedData)}],sequenceToken=logsToken)
      kin_response=kinesis_client.put_record(StreamName=kinesis_stream,PartitionKey=topic,Data = json.dumps(parsedData))
      cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': json.dumps(kin_response)}],sequenceToken=logsToken)
      time.sleep(10)
      return True
    def on_error(self, status):
      print('Error received:' + str(status))
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': status}],sequenceToken=logsToken)
      return True
    def on_limit(track):
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': track}],sequenceToken=logsToken)
      time.sleep(60)
      return True
    def on_disconnect_message(message):
      logs=cw_logs.describe_log_streams(logGroupName=logGroup,orderBy='LastEventTime',descending=True,limit=1)
      logsToken = logs['logStreams'][0]['uploadSequenceToken']
      cw_response = cw_logs.put_log_events(logGroupName=logGroup,logStreamName=logStream,logEvents=[{'timestamp': int(time.time()*1000),'message': message}],sequenceToken=logsToken)
      return True
  feedStream = TwitListener(bearer_token=BEARER_TOKEN)
  feedStream.add_rules(tweepy.StreamRule(topic))
  feedStream.filter(tweet_fields=['attachments','author_id','created_at','entities','geo','id','in_reply_to_user_id','lang','possibly_sensitive','source','text'])