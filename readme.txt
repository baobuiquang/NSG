List IMG                        docker images
List CON                        docker ps -a

Build IMG                       docker compose build
Run CON detached                docker compose up -d
Build IMG + Run CON detached    docker compose up -d --build
Stop CON + Remove CON           docker compose down

Remove everything               docker stop $(docker ps -a -q); docker rm -f $(docker ps -a -q); docker rmi -f $(docker images -q); docker volume rm -f $(docker volume ls -q); docker network rm $(docker network ls -q); docker system prune -a --volumes -f

Push to Docker Hub              1. docker login
                                2. docker tag imagelocal onelevelstudio/imagehub:tag01
                                3. docker push onelevelstudio/imagehub:tag01

docker tag docker-imagen onelevelstudio/imagen
docker push onelevelstudio/imagen