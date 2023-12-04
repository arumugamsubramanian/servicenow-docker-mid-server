# servicenow-docker-mid-server
A Docker Recipe for ServiceNow Mid Server


## Instruction to run mid server docker image

### Vancouver:
1. copy [mid.env.example](run%2Fmid.env.example) to mid.env
2. add secrets to mid.env
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
7. Now start the mid-server with below command from second time onwards
```shell
docker run -d --network="kind" --env-file run/mid.env \
  -v $(pwd)/run/snc_mid_server_container_files/snc_mid_server:/opt/snc_mid_server \
  --name mid_server \
  arumugamsubramanian/mid-linux:vancouver-07-06-2023__patch2-hotfix1-10-04-2023_10-06-2023_1235
```

### Utah - [utah-12-21-2022__patch7a-09-28-2023_10-10-2023_1258](https://hub.docker.com/layers/arumugamsubramanian/mid-linux/utah-12-21-2022__patch7a-09-28-2023_10-10-2023_1258/images/sha256-ce53e8d2fdbbf0eca7acd10693567bd030be54c7726c1066e3fa914a16bbf1ff?context=repo)
1. copy mid.env.example to mid.env
2. add secrets to mid.env
3. Run the docker image
```shell
docker run --env-file <env_file_name_here> <docker_tag or image_id>
```
4. First time running the mid-server

```shell
docker run -d --env-file run/utah/mid.env \
  -v $(pwd)/run/utah/snc_mid_server:/app \
  --name mid_server_utah \
  arumugamsubramanian/mid-linux:utah-12-21-2022__patch7a-09-28-2023_10-10-2023_1258
```
Note: Mount a local share folder to /app inside container to copy the content of mid server to host machine

5. Validate the mid-server and bring to green
6. Login into docker container
```shell
docker exec -it mid_server_utah bash
cd ..
cp -r snc_mid_server/* /app/
cp snc_mid_server/.container /app/
exit
docker stop mid_server_utah
```
7. Now start the mid-server with below command from second time onwards. I use KIND network because I run k8s cluster in kind network
```shell
docker run -d --network="kind" --env-file run/utah/mid.env \
  -v $(pwd)/run/utah/snc_mid_server:/opt/snc_mid_server \
  --name mid_server_utah \
  arumugamsubramanian/mid-linux:utah-12-21-2022__patch7a-09-28-2023_10-10-2023_1258
```