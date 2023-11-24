# servicenow-docker-mid-server
A Docker Recipe for ServiceNow Mid Server


## Instruction to run mid server docker image

1. Place the sensitive data in mid-secrets.properties
2. add secrets to [mid.env](run%2Fmid.env)
3. Run the docker image
```shell
docker run --env-file <env_file_name_here> <docker_tag or image_id>
```
4. First time running the mid server

```shell
docker run -d --env-file run/mid.env \
  -v $(pwd)/run/snc_mid_server_container_files/snc_mid_server:/app \
  --name mid_server \
  arumugamsubramanian/mid-linux:vancouver-07-06-2023__patch2-hotfix1-10-04-2023_10-06-2023_1235
```
Note: Mount a local share folder to /app inside container to copy the content of mid server to host machine

5. Validate the mid server and bring to green
6. Login into docker container
```shell
docker exec -it mid_server bash
cp -r snc_mid_server/ /app/
exit
docker stop mid_server
```
7. Now start the mid server with below command from second time onwards
```shell
docker run --env-file run/mid.env \
  -v $(pwd)/run/snc_mid_server_container_files/snc_mid_server:/opt/snc_mid_server \
  --name mid_server \
  arumugamsubramanian/mid-linux:vancouver-07-06-2023__patch2-hotfix1-10-04-2023_10-06-2023_1235
```
