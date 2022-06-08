# AWS Data Ingestion

This project will describe how to ingest IoT devices data into the AWS using IoT Core and Kinesis.  

## Table of Contents

- [AWS Data Ingestion](#aws-data-ingestion)
  * [Table of Contents](#table-of-contents)
  * [Overview](#overview)
    + [Prerequisites](#prerequisites)
  * [Tasks](#tasks)
    + [Defining  devices to IoT Core](#defining--devices-to-iot-core)
    + [Connecting simulated devices and sending  data using MQTT](#connecting-simulated-devices-and-sending--data-using-mqtt)
    + [Viewing simulated data in AWS.](#viewing-simulated-data-in-aws)
    + [Creating a  Kinesis Data Stream](#creating-a--kinesis-data-stream)
    + [Defining rules for moving data into Kinesis](#defining-rules-for-moving-data-into-kinesis)
    + [Reading Kinesis topics in Event Stream Processing](#reading-kinesis-topics-in-event-stream-processing)
      - [Generating an aws access key ID](#generating-an-aws-access-key-id)
      - [Setting up an STS Assume Role](#setting-up-an-sts-assume-role)
    + [Walk Through](#walk-through)
    + [Troubleshooting](#troubleshooting)
  * [License](#license)
  * [Additional Resources](#additional-resources)




## Overview

Suppose you would like to use  AWS IoT services to ingest and make available to a down stream analytics engine such as SAS Event Stream Processing.  What steps would you need to take to do so?  This project walks through the steps necessary in a test environment.    The following tasks will be discussed: 

- Defining devices to IoT Core
- Connecting simulated devices and sending  data using MQTT
- Defining rules for moving data into Kinesis
- Reading Kinesis topics in Event Stream Processing 

![image-20220412161339488](Images/image-20220412161339488.png)

### Prerequisites

This project assumes you have access to the following products and services.

- SAS Viya 2022.x.x

- AWS account with authority to create, IoT things, IAM, Kinesis topics 

- Node-Red server

  

## Tasks

### Defining  devices to IoT Core

In this section we will define a new thing in IoT Core and save off the necessary connection files needed to send data using MQTT.  

- Define a thing
- Define a thing type
- Define a thing group
- Security certificates



First log into your AWS account and search for IoT Core.   Once there expand the manage section on the left and click Things.  We will use this to create a thing.  

<img style="float: left;" src= "Images/image-20220412143037924.png"/>

From AWS > Manage > Things click the Create things button.  Let's create a single thing for now but you can use this interface to create many things at once if needed.   A Thing is  a digital twin of a physical device in AWS IoT.   Let's say you have a temperature and humidity sensor located in a kitchen freezer.  Since we are simulating the device in this project you can create any type of use case you like at this point.   Let's create a thing called freezer1 for now.   We will skip all the optional configurations for simplicity. 

![image-20220413094122029](Images/image-20220413094122029.png)

After clicking next you will be taken to the certificate panel.  Your device won't be able to connect to AWS IoT until it has an active certificate with an appropriate policy.   Click auto-generate certificates.

![image-20220413094502724](Images/image-20220413094502724.png)	

This will take you to the policy page.  You will also need a policy before you can connect so click Create policy here.  Create a generic freezer policy which allows all IoT actions on any resource as follows: 

![image-20220413095204912](Images/image-20220413095204912.png)	

Now that you have a policy you can attach it to your thing, in this case freezer1, when you create your thing.   Then click  the Create thing button. 

![image-20220413095827907](Images/image-20220413095827907.png)	

This will take you to the certificates and keys page.   Download all the items to a unique directory.  You will need to use these files in the simulator to connect to IoT Core using MQTT.   My files looks like this:  

![image-20220413100117896](Images/image-20220413100117896.png)	

Of course you names will vary.   Now your thing is ready! 



### Connecting simulated devices and sending  data using MQTT

Since I don't have a real temperature and humidity sensor I am going to simulate this device using Node-Red.  Our Node-Red project will consist of three nodes.  

- Inject:   Timer event to kick off the flow
- function:  This will generate our json
- mqtt out:  Send json over mqtt to AWS IoT Core using SSL.  

Simply drag the nodes from the node pallet onto the canvas.  

![image-20220413101234688](Images/image-20220413101234688.png)		

Next we will configure our mqtt node to communicate with AWS IoT Core.   Double click the mqtt node to open settings and a new mqtt-broker.  The broker host name is found on the AWS IoT > Settings page.



![image-20220413102233981](Images/image-20220413102233981.png)



Once you have the hostname, enter it as follows.  Be sure to use TLS and set the port to 8883. 

![image-20220413102947607](Images/image-20220413102947607.png)		

Since we must use TLS to connect to AWS IoT a TLS config needs to be created using the files we downloaded earlier.  Click the pen on the Use TLS line to open the configuration panel.   Upload the three files download in the previous steps. 

![image-20220413103635614](Images/image-20220413103635614.png)	

Once you click add you are almost done.  You just need to enter a topic name.  I chose freezers just in case I wanted to add a second freezer.  I could use the same topic. 

![image-20220413103857316](Images/image-20220413103857316.png)	

Click done.   On the top right hand side of the Node-Red interface click the deploy button.  This will deploy this flow to the node-js server.    If you have done all these steps correctly, and that is a big IF.  Your mqtt node will enter a connected state which means it can now communicate with AWS IoT Core!  Good job.  

![image-20220413104210106](Images/image-20220413104210106.png)	

Our flow is connected but does nothing.  We will use the function node to write some simple javascript which will simulate our freezer data.  Double click the function node to open the interface.   I have added a message payload that hard codes the temperature and humidity.  You can code up as fancy of simulator as you like.  In my world it is always warm and nice even inside of a freezer. 

![image-20220413110447691](Images/image-20220413110447691.png)	

```javascript
msg.payload = {"temperature": 90,"humidity": 65.2};
return msg;
```

My little flow now looks like this:   

![image-20220413110549968](Images/image-20220413110549968.png)	

Every time I hit the button on the left of the timestamp node a new event is generated and sent to AWS IoT.     IoT is so much fun, I can hardly stand it. :) 

### Viewing simulated data in AWS. 

Now that we can send in data let's view that data in AWS IoT.   For this we will use the MQTT test client on AWS.  Navigate to AWS IoT > MQTT test client on your AWS console.   Enter your Topic filter under Subscribe  to a topic and click subscribe.   My topic was called freezers so that is what I subscribed to.   Once subscribed hit the timestamp button a few times and watch the events roll in. 

![image-20220413111730197](Images/image-20220413111730197.png)	

### Creating a  Kinesis Data Stream

Kinesis Data Streams is a message bus that was models after Kafka where a shard is analogous to a partition.   In our use case we will forward incoming IoT data from a single mqtt topic to a Kinesis stream.  However, in a scaled up customer implementation, 100s of mqtt topics might be funneled into various Kinesis streams for downstream processing.   

Navigate to the [Kinesis Console](https://console.aws.amazon.com/kinesis)

Select **Create data stream** to navigate to the Amazon Kinesis Data Stream service

![image-20220413141843333](Images/image-20220413141843333.png)	

Choose **freezer_data** as the stream name. 

Enter 4 for the number of shards.  A shard can process about 1000 records per second and output twice that many.  So our 4 shards should be able to input 4000 records per second and output 8000.  

Next click the **Create data stream** button.  

After a few minutes your stream will be created and set to active with the following settings: 

![image-20220413142615300](Images/image-20220413142615300.png)	

```
arn:aws:kinesis:us-east-1:299238628350:stream/freezer_data
```

Please note that the new stream is created under the main AWS account number and not associated to the user which is logged on and creating this resource.   This means there isn't an easy way to clean up resources on AWS without deleting the main AWS account which will effect all the users of this account.  

### Defining rules for moving data into Kinesis

We now how have created our Kinesis stream, next we need to redirect messages from our AWS IoT topic freezers to it.   This is done by creating a rule in AWS IoT.

Navigate to **AWS IoT > Rules** and select **Create.**

Name your rule and then edit the SQL statement to select on the topic we created earlier.  In my case, that topic was freezers.

```sql
SELECT * FROM 'freezers'
```

Next add an action.  Actions define what will happen when the select statement above contains messages.  We are going to pick the action to forward to Kinesis. 

![image-20220413162019350](Images/image-20220413162019350.png)	

At the bottom of the page there is a Configure **action button**, press it. 

Enter the Stream name created earlier. 

![image-20220413163655281](Images/image-20220413163655281.png)	

We will need to create a new IAM role to authorize this action access to our new Kinesis stream.  Select **Create Role.**

![image-20220413163920679](Images/image-20220413163920679.png)	



Now select **Add action**.  This will take you back to the Create rule page.  

Select **Create rule** at the bottom.

The rule will now be actively sending messages to our Kinesis stream.  Please navigate to the Kinesis dashboard and check the metrics to ensure the data is flowing.  The graph might look like this: 

![image-20220413172455866](Images/image-20220413172455866.png)	



### Reading Kinesis topics in Event Stream Processing 

The ESP Kinesis connector supports 2 different authentication methods.  

1. aws access key id 
2. sts assume role 

The first method requires that a temporary token is generated and used to make the connection.  This token is generally very short lived.  For example, a token might only be valid for 5 minutes.   If an ESP project doesn't start before the 5 minute interval expires the project connection will fail.  

Method 2 also uses a temporary token but generates it internally during the API call.  This allows an ESP project to be restarted without a token being created separately.   However, it requires that an STS assume role is set up on the AWS cloud to support this use case.   The STS assume role associates an AWS user with the assume role policy.   The ESP project must make the connection to AWS using an Access key ID created for this user.   It is **very important** that the user created for the assume role be created with minimal privileges.  Specifically, only giving the user the ability to access the one needed resource.  If this user has the ability to create other types of resources and does so there is no way to easily track and clean up any damage that might be done because AWS creates things under the main ID and they are not tied to specific users.     

More details on STS Assume roles may be found here:  https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html

#### Generating an aws access key ID

In order to connect to the Kinesis data stream these 3 properties must be generated:

![image-20220426135500735](Images/image-20220426135500735.png)	

These properties may be generated from AWS Cloudshell using the following commands.   The main command that need to be issued is as follows:   **aws sts get-session-token --duration-seconds 129600,** where 129600 is the maximum allowable time of 36 hours. 

```bash
aws configure
AWS Access Key ID [None]: AKIAULLAEDP7COM4DMXC
AWS Secret Access Key [None]: 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
Default region name [None]: us-east-1
Default output format [None]: 
[cloudshell]$ aws sts get-session-token --duration-seconds 129600
{
    "Credentials": {
        "AccessKeyId": "ASIAULLADDP7FFFFFFFF",
        "SecretAccessKey": "r0UuFB2eHNOI1XAlu5IW+NnrhpBJx3+uKFFFFFVB",
        "SessionToken": "dummykeyluX2VjEPT//////////wEaCXVzLWVhc3QtMSJHMEUCIQCRYsjpdIde2JHQrI9BawMVqtLdATSb+rgOfRwh9r0+cwIgDI3jFSqptnV7kevD5g3XajM8+k6E+by6QKxuQSA70HEq9AEIrf//////////ARABGgwyOTkyMzg2MjgzNTAiDGEvdJULkeMnNm7QxSrIAbZ2MiPKdQja3K+tU2BYNx27nFsZs5DJ7pQFgk7AXysUnlGePNAdIrSbw0sseMsVIGhDLR9DeaNvMrQnMW+8V7fXCWuEHqW2uWQnp+XmyNvkzNfuhRmnRCPiYzjTvhkvs4KnoCwv1IP9wsTnAipY9zAgly/xJT7K6lCPiuLHIRksjuom30iLTuGwmfsSs+aSLkcIUxlinWIOXP4qrrqnA3408Upf4RaNEZMngdSV4UzgyK8WKYoB1xaF2800ZgL37aAHD7QkqLXlMOCdoZMGOpgBcefwIonL8i8M9tDjLZgOn/E3WO+4CxPKpiNaXxZC45rjkoJpiXiVeujOayhUJSihBwY+l/zSlyVWvB5yt0F0xSSrnwES5fGUZa1ou1Y2rvdQo3vgiWrvCV3jLAOG1i8/23SBDX8c7SrH9NkSJmF82PY7iDHlKNaRaOWTYCe6qFXO2g39wxgRz5YFU6brsQ5e7XIAg3b8Ans=",

```

The AWS Access Key ID entered into the aws configure command is not the one used by ESP.   This is generated from the IAM console under a user that has rights to access the Kinesis stream in question.  It can be generated here: 

![image-20220426155737389](Images/image-20220426155737389.png)	

Once the aws sts get-session-token --duration-seconds 129600 command is entered it will generate a new temporary set of credentials that will be used by the ESP Kinesis connector.  

An example of the ESP connector definition is as follows: 

```xml
<connector class="kinesis" name="New_Connector_1">
      <properties>
        <property name="type"><![CDATA[pub]]></property>
        <property name="awsaccesskeyid"><![CDATA[ASIAULLADDP7FFFFFFFF]]></property>
        <property name="awssecretkey"><![CDATA[r0UuFB2eHNOI1XAlu5IW+NnrhpBJx3+uKFFFFFVB]]></property>
        <property name="awssessiontoken"><![CDATA[dummykeyluX2VjEPT//////////wEaCXVzLWVhc3QtMSJHMEUCIQCRYsjpdIde2JHQrI9BawMVqtLdATSb+rgOfRwh9r0+cwIgDI3jFSqptnV7kevD5g3XajM8+k6E+by6QKxuQSA70HEq9AEIrf//////////ARABGgwyOTkyMzg2MjgzNTAiDGEvdJULkeMnNm7QxSrIAbZ2MiPKdQja3K+tU2BYNx27nFsZs5DJ7pQFgk7AXysUnlGePNAdIrSbw0sseMsVIGhDLR9DeaNvMrQnMW+8V7fXCWuEHqW2uWQnp+XmyNvkzNfuhRmnRCPiYzjTvhkvs4KnoCwv1IP9wsTnAipY9zAgly/xJT7K6lCPiuLHIRksjuom30iLTuGwmfsSs+aSLkcIUxlinWIOXP4qrrqnA3408Upf4RaNEZMngdSV4UzgyK8WKYoB1xaF2800ZgL37aAHD7QkqLXlMOCdoZMGOpgBcefwIonL8i8M9tDjLZgOn/E3WO+4CxPKpiNaXxZC45rjkoJpiXiVeujOayhUJSihBwY+l/zSlyVWvB5yt0F0xSSrnwES5fGUZa1ou1Y2rvdQo3vgiWrvCV3jLAOG1i8/23SBDX8c7SrH9NkSJmF82PY7iDHlKNaRaOWTYCe6qFXO2g39wxgRz5YFU6brsQ5e7XIAg3b8Ans=]]></property>
        <property name="kinesistype"><![CDATA[json]]></property>
        <property name="streamname"><![CDATA[freezer_data]]></property>
        <property name="awsregion"><![CDATA[us-east-1]]></property>
        <property name="sharditeratortype"><![CDATA[latest]]></property>
      </properties>
    </connector>
```

#### Setting up an STS Assume Role

Using an STS assume role is a better solution for your project because it removes the task of generating a temporary token that is only valid for at most 36 hours.  However, there are many steps to enabling this option.  

First we must add an assume role  policy to a user which will provide access to the local resource.   This policy is added to the user under the Permissions tab and looks like this: 

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:kinesis:us-east-1:299238628350:stream/freezer_data"
        }
    ]
}
```

Next create a role that will be used to create a trust relationship between the user assuming the role and a resource.  In this case, one Kinesis steam.   Under IAM > Roles  click Create role.  The role will have 2 different sections.  First is the Permissions tab.  This will list what the role allows a user to do.  For this demo I opened to up but you can limit access as well. 

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "kinesis:*",
            "Resource": "*"
        }
    ]
}
```

Now that we have defined what the user can do, let's set up a trust relationship between a user and the sts:Assumerole.  This is where the ExternalID is defined that is used on the adapter/connector settings in ESP. 

```json
	{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::299235628350:user/NewUser.forAssumerole@sas.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "VeryUniqueID1"
                }
            }
        }
    ]
}
```



Once all those steps are complete you need to create an AWS Access Key ID for the user that has the  assume role defined.  This is generated from the IAM console under a user that has rights to access the Kinesis stream in question.  It can be generated here: 

![image-20220426155737389](Images/image-20220426155737389.png)	

Once created these items are entered as the following environment variables in ESP studio.  For example: 

![image-20220427155708001](Images/image-20220427155708001.png)	

These keys will show up as exported variables in the Linux pod which is running ESP and be used by the adapter/connector during the establishment of the Kinesis connection.   Future versions of ESP will allow you to specify these keys in the connector properties and dynamically create the export variables before the ESP project is started. 

Our ESP connector definition now looks as follows: 

```xml
<connector class="kinesis" name="New_Connector_1">
      <properties>
        <property name="type"><![CDATA[pub]]></property>
        <property name="stsassumerolearn"><![CDATA[arn:aws:iam::299238628350:role/stsassumeroleforkinesis]]></property>
        <property name="stsassumerolesessionname"><![CDATA[anything]]></property>
        <property name="stsassumeroleexternalid"><![CDATA[VeryUniqueID1]]></property>
        <property name="kinesistype"><![CDATA[json]]></property>
        <property name="streamname"><![CDATA[freezer_data]]></property>
        <property name="awsregion"><![CDATA[us-east-1]]></property>
        <property name="sharditeratortype"><![CDATA[latest]]></property>
      </properties>
    </connector>
```

You can see we are now using the stsassumerole* properties instead of the awsaccesskey* properties as defined above.  



### Walk Through

Once everything is configured you simply have to start the ESP project which will read data from your Kinesis stream.  In my case that is called freezer_data.  I defined 2 shards for my stream, therefore the ESP messages in the log are as follows: 

```bash
dfESPconnector::setState(): Connector New_Connector_1 in default connector group has new state: running
2022-04-26T20:06:59.638Z
INFORMATIONAL
 dfESPkinesisConnector::shardIdThread(): Updated number of shards from 0 to 1
2022-04-26T20:06:59.639Z
INFORMATIONAL
 C_dfESPpubsubInit(): Successfully loaded pubsub plugin libesp_json_ppi.so from /opt/sas/viya/home/SASEventStreamProcessingEngine/lib/plugins/
2022-04-26T20:06:59.639Z
INFORMATIONAL
 dfESPkinesisConnector::shardIdThread(): Updated number of shards from 1 to 2
```

This indicates that the connector is in a state of running.  

Now let's generate some events from node-red in order to see them flow into ESP.  

![image-20220426161528902](Images/image-20220426161528902.png)	

We have 2 flows in node-red.  The top flow in the red box sends data through MQTT to AWS IoT Core.   From IoT Core there is a rule set up which forwards the events to Kinesis.  The second flow in green sends data directly to Kinesis.  

Each time the boxes inside the purple circles are pressed an event is sent.   

Let's hit the grey boxes a few times and see what we get in ESP Studio. 

![image-20220426162341120](Images/image-20220426162341120.png)



I hit each button once and got one event from each source.  I think one freezer isn't even turned on!

Whether you send messages through AWS IoT Core or send messages directly to Kinesis ESP is updated and empowers down stream analytics.  

### Troubleshooting

**There is so much that can go wrong**.   There are 1000 steps to getting this working.  Just be as careful as possible and cross your fingers.   If all else fails configure a CloudTrail for your services and point all the services to it.  That will give you a chance to look at the AWS logs for each service.  

## License

> This project is licensed under the [SAS License Agreement for Corrective Code or Additional Functionality](LICENSE).

## Additional Resources



* [AWS IoT Core](https://aws.amazon.com/iot-core/)	
* [AWS Kinesis](https://aws.amazon.com/kinesis/)
* [Node-Red](https://nodered.org/)
* [Node-Red for AWS nodes](https://flows.nodered.org/node/node-red-contrib-aws)
* [ESP Kinesis connector](https://go.documentation.sas.com/doc/en/espcdc/v_021/espca/p1g1ixn7gjmbnpn1v0zgi3uftx1d.htm)
* [STS assume role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html)
