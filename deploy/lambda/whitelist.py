import json
import boto3
import botocore
from botocore.vendored import requests

# Config global var before deployment
REMOVE_PORTS = []
WHITELIST_SERVICE = 'https://my.service.org/whitelist'


def get_nodes_ips():
    data = requests.get(url=WHITELIST_SERVICE)
    return json.loads(data.json()['body'])


def get_ip_perm_module(ip):
    return {
        'IpProtocol': "tcp",
        'FromPort': 11625,
        'ToPort': 11625,
        'IpRanges': [{'CidrIp': ip, 'Description': f'Node - {ip}'}]
    }


def generate_ip_permissions():
    ip_permissions = [get_ip_perm_module(ip) for ip in get_nodes_ips()]
    return ip_permissions


def remove_rules_from_sg(security_group):
    try:
        rules_to_delete = []
        for rule in security_group.ip_permissions:
            from_port = rule.get('FromPort')
            to_port = rule.get('ToPort')
            if from_port in REMOVE_PORTS or to_port in REMOVE_PORTS:
                rules_to_delete.append(rule)
        security_group.revoke_ingress(IpPermissions=rules_to_delete) if rules_to_delete else None
    except Exception as e:
        print(f"Failed revoke ingress {e.__str__()}")
        raise e


def lambda_handler(event, context):
    '''
    lambda function to deploy cores ip rules in a security group.
    Missing global scope params: REMOVE_PORTS and WHITELIST_SERVICE
    :param REMOVE_PORTS: list[int], list of ports to be removed
    :param WHITELIST_SERVICE: str, service url to receive list of cores ips
    :param event: dict, lambda param, holds key val of SECURITY_GROUP_ID and REGION_NAME
    :return: http response
    '''
    try:
        try:
            SECURITY_GROUP_ID = event['SECURITY_GROUP_ID']
            REGION_NAME = event['REGION_NAME']
        except Exception as e:
            print(f"Failed get event params {e.__str__()}")
            raise e
        try:
            ec2_resource = boto3.resource('ec2', region_name=REGION_NAME)
            security_group = ec2_resource.SecurityGroup(SECURITY_GROUP_ID)
        except Exception as e:
            print(f"Failed create sg client{e.__str__()}")
            raise e
        remove_rules_from_sg(security_group)
        try:
            security_group.authorize_ingress(GroupId=SECURITY_GROUP_ID,
                                             IpPermissions=generate_ip_permissions())
        except botocore.exceptions.ClientError as e:
            print(f"Duplicate ip {e.__str__()}")
    except Exception as e:
        return {
            'statusCode': 501,
            'body': json.dumps(f"Failed update nodes whitelist {e.__str__()}")
        }
    return {
        'statusCode': 200,
        'body': json.dumps(f"Active ips {security_group.ip_permissions}")
    }
