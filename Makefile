up:	
	sudo docker-compose -p vacancy -f deploy/docker-compose-dev.yml up --build -d

up_log:
	sudo docker-compose -p vacancy -f deploy/docker-compose-dev.yml up --build

down:
	sudo docker-compose -p vacancy -f deploy/docker-compose-dev.yml down

logs:
	sudo docker-compose -p vacancy -f deploy/docker-compose-dev.yml logs -f --tail 30

graylog_start:
	sudo docker-compose -p graylog -f deploy/docker-compose-log.yml up --build

graylog_stop:
	sudo docker-compose -p graylog -f deploy/docker-compose-log.yml down