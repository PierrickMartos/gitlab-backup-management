# Gitlab project backup management

Gitlab project backup management is a python tool for Gitlab to backup all (or some) of your projects into AWS S3. The tool enable you to define 
which groups you want to backup and automatically loop through them to backup all projects and send the archive on AWS S3.

We also provide a Docker image so that you can be able to run it easilly. Finally, we also provide a full guide to setup 
the tool on AWS Lambda.

## Install

The only requirements is `Docker`. Then, just clone this repository.

## Configuration

You only need to set several environment variables in order to make the script works. Those argument will be pass to Docker 
container.

Five environment variables must be set:
- `AWS_ACCESS_KEY_ID`: AWS access key id with RW permissions on the targeted bucket
- `AWS_SECRET_ACCESS_KEY`: AWS secret key with RW permissions on the targeted bucket
- `GITLAB_TOKEN`: the Gitlab token to interact with the API
- `GROUPS_TO_BACKUP`: the Gitlab groups id to backup (you can set one group or several groups ids by splitting them with comma)
- `AWS_S3_BUCKET`: the bucket name where the backup will be stored

There is also **one optional env var**:
- `GITLAB_URL`: by default, this value is set to `https://gitlab.com`. You can use this env var if you want to backup your 
on-premise Gitlab.

Example:
```
GITLAB_TOKEN=xxx
GROUPS_TO_BACKUP=42,12
AWS_S3_BUCKET=gitlab_projects_backup
AWS_ACCESS_KEY_ID=xxxx
AWS_SECRET_ACCESS_KEY=xxx
```

## Usage

### Locally (through Docker)

Build your image:
```bash
docker build -t gitlab-backup .
```

Run your image locally (args order are important, --env needs to be before docker image):
```bash
docker run --env GITLAB_TOKEN=xx --env GROUPS_TO_BACKUP=42 --env AWS_S3_BUCKET=gitlab_projects_backup \
    --env AWS_ACCESS_KEY_ID=xx --env AWS_SECRET_ACCESS_KEY=xx -p 9000:8080 --name gitlab-backup gitlab-backup 
```

In a separate terminal, you can then locally invoke the function using cURL:
```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

### AWS Lambda (with scheduling through Cloudwatch event)

The objective is to setup an AWS Lambda to execute backup on a regular basis with AWS Cloudwatch (every 24 hours for eg).

1. First, you need to create a registry in Amazon Container Services. Then, copy the `URI` of your private registry.

2. Authenticate the Docker CLI to your Amazon ECR registry (replace accordingly the region and the ECR URI from previous copy):
```bash
aws ecr get-login-password --region [us-east-1] | docker login --username AWS --password-stdin [123456789012.dkr.ecr.us-east-1.amazonaws.com]
```

3. Tag your image to match your repository name, and deploy the image to Amazon ECR using the docker push command (replace accordingly the region and the ECR URI):
```bash
docker tag gitlab-backup:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/gitlab-backup:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/gitlab-backup:latest
```

4. Now, you can see your docker image in the ECR repository.
PS: you can find those commands in the repository page, by clicking "View push commands" button in top right.

5. Create a lambda function by selecting "Container image", set a lambda name and select your image just uploaded.

6. You need to define environment variables in the Lambda console, please follow the steps here:
https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-config. See the [#Configuration](#Configuration) section for the list of env vars needed to be set.

**Note: you need to set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` only if the lambda role don't have permissions 
to write on your bucket.** Best is to set permissions on the created lambda role.

7. Increase timeout, since Gitlab API have rates limit, we cannot export more than 6 projects per minutes. So depending 
of the volume of projects you want to export, you'll need to improve lambda timeout. 

8. Test the whole thing by sending a test event.

9. Setup a cloudwatch event to launch your Lambda on a regular basis: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html

10. Done!

## Debug

View logs:
```bash
docker logs gitlab-backup
```

## Extra

### Remove/archive exports after a period
AWS S3 is really helpfull on managing lifecycle of yours backups. If you want to delete or archive (To Glacier for example)
your backups, the best is to rely on AWS S3 lifecycle (with object expiration).

- [Managing your storage lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

**Example: delete exports after 1 year**

Create a lifecycle rule that applies to all objects in the bucket, set "Expire current versions of objects" after 360 
days and set "Permanently delete previous versions of objects" after 1 day.

### Enable encryption and versioning on your AWS S3 bucket
We really recommends you to enable encryption and versioning on the bucket that will store your exports.

- [Enabling Amazon S3 default bucket encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html)
- [Enabling versioning on buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/manage-versioning-examples.html)

### AWS S3 replication

This tool will export your projects to AWS S3, that's a really great starting point. It's recommended to enable replication 
to a bucket in another region.

- [Configuring replication on AWS S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-example-walkthroughs.html)

## What is and is not included in backup

Here you can find [the exported contents in project export](https://docs.gitlab.com/ee/user/project/settings/import_export.html#exported-contents).

## How it works

1. Send a request to Gitlab API to retrieve groups
2. Loop through all groups and get from Gitlab API group's projects
3. For each project, generate a presigned URL on AWS S3 for upload (PUT)
4. Schedule a project export through the Gitlab API by sending the presigned S3 URL for direct upload
5. Exports will be automatically upload to AWS S3. The dir structure of uploaded exports will used the `path_with_namespace` 
of Gitlab project (https://docs.gitlab.com/ee/api/projects.html) and the filename will be the current date (`Y-m-d-H-i-s.gz`). 

Note: Gitlab API have a rates limit on project export, 6 max every minute. The script automatically manage this with a sleep
 of 1 minute every 6 projects. 

## Dependencies

- Boto3: AWS SDK for python
- python-gitlab: python library for Gitlab API

## Resources

- [Project export API documentation](https://docs.gitlab.com/ee/api/project_import_export.html)
- [Gitlab python library documentation](https://python-gitlab.readthedocs.io/)
- [Boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html)

## Contributing

GitlabBackupManagement is an open source project. Contributions made by the community are welcome. Send us your ideas, 
code reviews, pull requests and feature requests to help us improve this project.

## License

GitlabBackupManagement is free to use and is licensed under the [MIT license](http://www.opensource.org/licenses/mit-license.php)
