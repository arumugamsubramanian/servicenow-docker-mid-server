## Instruction to run mid server docker image

1. Place the sensitive data in mid-secrets.properties
2. add secrets to [mid.env](mid.env)
3. Run the docker image
```shell
docker run --env-file <env_file_name_here> <docker_tag or image_id>

docker run --env-file run/mid.env arumugamsubramanian/mid-linux:vancouver-07-06-2023__patch2-hotfix1-10-04-2023_10-06-2023_1235
```