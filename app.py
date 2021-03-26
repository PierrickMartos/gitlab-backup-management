from os import environ
import gitlab
import time
import boto3
from datetime import datetime

now = datetime.now()

if not 'GITLAB_TOKEN' in environ:
    print('You need to set "GITLAB_TOKEN" env var')
    exit(1)

if not 'GROUPS_TO_BACKUP' in environ:
    print('You need to set "GROUPS_TO_BACKUP" env var. You can pass one group or several split by comma')
    exit(1)

if not 'AWS_S3_BUCKET' in environ:
    print('You need to set "AWS_S3_BUCKET" env var. Just the bucket name, script automatically get the bucket\'s region.')
    exit(1)

if not 'AWS_ACCESS_KEY_ID' in environ:
    print('You need to set "AWS_ACCESS_KEY_ID" env var.')
    exit(1)

if not 'AWS_SECRET_ACCESS_KEY' in environ:
    print('You need to set "AWS_SECRET_ACCESS_KEY" env var.')
    exit(1)

gitlab_url = 'https://gitlab.com'
if 'GITLAB_URL' in environ:
    gitlab_url = environ.get('GITLAB_URL')

project_export_limit_per_minute = 6
projects_exported_count = 1

def create_presigned_url(bucket_name, object_name, expiration=10800):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    s3_client = boto3.client('s3')
    response = s3_client.get_bucket_location(Bucket=bucket_name)

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', region_name=response['LocationConstraint'])
    return s3_client.generate_presigned_url(ClientMethod='put_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)

def export_project(projectId):
    global projects_exported_count
    p = gl.projects.get(projectId)
    print('Launching export for ' + p.name + '...')
    upload_url = create_presigned_url(environ.get('AWS_S3_BUCKET'), str(p.path_with_namespace) + '/' + now.strftime("%Y-%m-%d-%H-%M-%S") + '.tgz')
    # Schedule an export to AWS S3
    p.exports.create({'upload': {'url': upload_url}})
    if (projects_exported_count == project_export_limit_per_minute):
        print('Export limit per minute reached, wait for 60 seconds...')
        time.sleep(60)
        projects_exported_count = 0
    projects_exported_count = projects_exported_count + 1
    print('Export launched for ' + p.name + ', moving to next project.')
    print('')

gl = gitlab.Gitlab(gitlab_url, private_token=environ.get('GITLAB_TOKEN'))

groups_to_backup = environ.get("GROUPS_TO_BACKUP").split(",")

# Loop through all groups and projects to launch exports (one per project)
for groupId in groups_to_backup:
    group = gl.groups.get(groupId)
    projects = group.projects.list()
    if projects:
        for project in projects:
            export_project(project.id)
