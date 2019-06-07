import boto3
import cfnresponse


DEFAULT_LISTENER_PORT = 80


def lambda_handler(event, context):
    success = True
    data = {}
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            print(event['RequestType'] + " resource using NLB private IPs")
            nlb_description = event['ResourceProperties']['nlbDescription']
            listener_port = event['ResourceProperties']['listenerPort'] or DEFAULT_LISTENER_PORT
            print("Resource properties: listenerPort={}, nlbDescription={}".format(listener_port, nlb_description))
            client = boto3.client('ec2')
            nlb_nis = client.describe_network_interfaces(Filters=[
                {
                    'Name': 'description',
                    'Values': ['*' + nlb_description + '*']
                }
            ], MaxResults=100)
            data = {
                'privateIps': [{
                    'IpProtocol': 'tcp',
                    'CidrIp': ni['PrivateIpAddress'] + '/32',
                    'FromPort': listener_port,
                    'ToPort': listener_port
                } for ni in nlb_nis['NetworkInterfaces']]
            }
        else:
            print('Deleting resource, nothing to do')
        cfnresponse.send(event, context, cfnresponse.SUCCESS, data)
    except Exception as exception:
        print("Exception finding the private IPs of the NLB", str(exception))
        data = {}
        success = False
    finally:
        status_response = cfnresponse.SUCCESS if success else cfnresponse.FAILED
        print("Cloudformation status response: " + status_response)
        cfnresponse.send(event, context, status_response, data)
