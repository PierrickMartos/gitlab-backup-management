# Gitlab backup management

Gitlab backup management is a python tool for Gitlab to backup all your projects into AWS S3. The tool enable you to define 
which groups you want to backup and automatically loop through them to backup all projects and send the archive on AWS S3.

We also provide a Docker image so that you can be able to run it easilly. Finally, we also provide a full guide to setup 
the tool on AWS Lambda.

## Install



### Configuration

You need to set three environment variables:
- `AWS_ACCESS_KEY_ID`: AWS access key id
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `GITLAB_TOKEN`: the Gitlab token to interact with the API
- `GROUPS_TO_BACKUP`: the Gitlab groups id to backup (you can set one group or several by splitting them with comma)
- `AWS_S3_BUCKET`: the bucket name where the backup will be stored

Example:
```
GITLAB_TOKEN=xxxxxxxx
GROUPS_TO_BACKUP=42,12
AWS_S3_BUCKET=gitlab_projects_backup
```

## Usage

### Locally

Build your image:
```bash
docker build -t gitlab-backup .
```

Run your image locally (args order are important, --env needs to be before docker image):
```bash
docker run --env GITLAB_TOKEN=xx --env GROUPS_TO_BACKUP=42 --env AWS_S3_BUCKET=gitlab_projects_backup --env AWS_ACCESS_KEY_ID=xx --env AWS_SECRET_ACCESS_KEY=xx -p 9000:8080 --name gitlab-backup gitlab-backup 
```

In a separate terminal, you can then locally invoke the function using cURL:
```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

View logs:
```bash
docker logs gitlab-backup
```

### AWS Lambda



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