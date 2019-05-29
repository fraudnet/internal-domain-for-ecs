#!/usr/bin/env python3

# https://gist.github.com/chrisguitarguy/e9cb271f6ac882627d0d61efe03dc8ae was used as inspiration

import argparse
import requests
import os
import boto3 as aws

def _parse_args(args=None):
    p = argparse.ArgumentParser(description='Update a hostname record in route53 with the current IP address of instances in cluster')
    p.add_argument("cluster_name", help="Cluster name" )
    p.add_argument('zone_id', help='The DNS zone id to update')
    p.add_argument('hostname', help='The DNS name to update')

    return p.parse_args(args)


def _get_local_ipv4s(cluster_name):
    client = aws.client('ecs')
    ec2_client = aws.client('ec2')
    ips = []
    ec2_instances_ids = []
    r = client.list_container_instances(
        cluster = cluster_name
    )
    r = client.describe_container_instances(
        cluster = cluster_name,
        containerInstances = r["containerInstanceArns"]
    )
    for instance in r["containerInstances"]:
        ec2_instances_ids.append(instance["ec2InstanceId"])

    r = ec2_client.describe_instances(
        InstanceIds=ec2_instances_ids
    )
    for reservation in r["Reservations"]:
        for instance in reservation["Instances"]:
            ips.append(instance["PrivateIpAddress"])
    return ips


def _update_dns(ips, zone_id, hostname):
    dns = aws.client('route53')
    dns.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Comment': 'Update {} record from ASG'.format(hostname),
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': hostname,
                    'Type': 'A',
                    'TTL': 60,
                    'ResourceRecords': [{'Value':ip} for ip in ips],
                },
            }],
        },
    )


def main(args=None):
    args = _parse_args(args)
    ips = _get_local_ipv4s(args.cluster_name)

    _update_dns(ips, args.zone_id, args.hostname)


if __name__ == '__main__':
    main()
