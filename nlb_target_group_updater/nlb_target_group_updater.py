import boto3


def lambda_handler(event, context):
    port, alb_description, nlb_target_group_arn = __get_parameters_from(event)

    alb_ips = __get_alb_ips_from(alb_description)

    client = boto3.client('elbv2')
    nlb_target_group_health = client.describe_target_health(
        TargetGroupArn=nlb_target_group_arn
    )

    current_ips = __get_ips_from(nlb_target_group_health)
    client.register_targets(
        TargetGroupArn=nlb_target_group_arn,
        Targets=__create_targets_from(alb_ips, port)
    )

    invalid_ips = set(current_ips) - set(alb_ips)
    if len(invalid_ips) > 0:
        client.deregister_targets(
            TargetGroupArn=nlb_target_group_arn,
            Targets=__create_targets_from(invalid_ips, event['targetPort'])
        )


def __get_parameters_from(event):
    port = event['targetPort']
    alb_description = event['albDescription']
    nlb_target_group_arn = event['nlbTargetGroupArn']
    print("albDescription:", alb_description)
    print("targetPort:", port)
    print("nlbTargetGroupArn:", nlb_target_group_arn)
    return port, alb_description, nlb_target_group_arn


def __get_alb_ips_from(alb_description):
    client = boto3.client('ec2')
    alb_nis = client.describe_network_interfaces(Filters=[
        {
            'Name': 'description',
            'Values': ['*' + alb_description + '*']
        }
    ], MaxResults=100)
    return [ni['PrivateIpAddress'] for ni in alb_nis['NetworkInterfaces']]


def __create_targets_from(ips, port):
    return [{'Id': ip, 'Port': int(port)} for ip in ips]


def __get_ips_from(current_targets):
    return [target['Target']['Id']
            for target in current_targets['TargetHealthDescriptions']]
