import boto3
sts = boto3.client("sts")
print(sts.get_caller_identity())
s3 = boto3.client("s3")
for b in s3.list_buckets()["Buckets"]:
    print(b["Name"])