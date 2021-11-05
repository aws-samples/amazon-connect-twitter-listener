# Amazon Connect Twitter integration
This project contains source code and supporting files for twitter streaming to Amazon Connect Tasks. Tweets are filtered on the specified tag and analyzed using comprehend to identify language and sentiment. Both tags are added as attributes to the task so additional branching decisions can be made.

## Deployed resources

The project includes a cloud formation template with a Serverless Application Model (SAM) transform to deploy resources as follows:

### AWS Lambda functions

- Stream-Processor: Puts received filtered messages on task queue as specified on the ConnectTwitterConfig secret.
- Twitter-Replier: Posts back on publication.

### Kinesis Stream
- ConnectTwitterStream: Kinesis Stream for receiving the filtered messages.

### Secrets Manager Secret
- ConnectTwitterConfig: Secret for managing Twitter Streaming API access credentials, Kinesis stream, Amazon Connect configuration and topic to be monitored.

### EC2 Instance
- TwitterListener: EC2 instance running a python script using Tweepy for connecting to Twitter API. The script is configured by the CloudFormation template to start at instance boot up. The instance is created on the default VPC.

![](/imgs/twitter-listener.png)

## Prerequisites.
1. Amazon Connect Instance already set up with a queue and contact flow for handling tasks.
![](/imgs/contactflow-social.png)
2. Routing profile on Amazon Connect Instance with tasks enabled.
![](/imgs/routing-profile.png)
3. Twitter developer [account](https://developer.twitter.com/en). You'll need read and write permissions for the App created.
4. AWS Console Access with administrator account.
5. Cloud9 IDE or AWS and SAM tools installed and properly configured with administrator credentials.
6. KeyPair for the EC2 instance.

## Deploy the solution
1. Clone this repo.

`git clone https://github.com/aws-samples/amazon-connect-twitter-listener`

2. Build the solution with SAM.

`sam build -u` 

3. Deploy the solution.

`sam deploy -g`

SAM will ask for the name of the application (name it something relevant such as "Connect-Twitter") as all resources will be grouped under it and deployment region.Reply Y on the confirmation prompt before deploying resources. SAM can save this information if you plan un doing changes, answer Y when prompted and accept the default environment and file name for the configuration.

4. From the AWS Secrets Manager console, fill in the parameters in the **ConnectTwitterConfig** secret. The following parameters must be completed: **Instance ID** and **contact flow id** to handle tasks; Access Token, Access Token Secret, Consumer Key and Consumer Secret from the Twitter App; and the Twitter topic to monitor such as **#AWSRules**.
5. Add the **Twitter-Replier** function to the Amazon Connect configuration. You can use
![](/imgs/add-function-connect.png)
6. Create a new Transfer To Queue contact flow in Amazon Connect. Add a block for invoking the Twitter-Replier function. Name it TwitterReply.
![](/imgs/transfer-to-queue.png)
7. Create a Quick Connect with destination Queue and the TwitterReply contactflow created in the previous step.
![](/imgs/quick-connect.png)
8. Reboot the EC2 instance. This will start the python script, which will pull the configuration from the secret and it will start streaming data onto the Kinesis stream.
9. Agents enabled for tasks working on the associated Queue will receive tweets in the form of tasks. After accepting the task, the agent can reply back to Tweets using the TwitterReply quick connect to transfer the task. Information entered as part of the description will be posted on the Tweet being replied to.

## Resource deletion
1. Back on the cloudformation console, select the stack and click on Delete and confirm it by pressing Delete Stack. 
