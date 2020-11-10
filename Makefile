up:	
	docker-compose -p vacancy -f deploy/docker-compose-dev.yml up --build -d

up_log:
	docker-compose -p vacancy -f deploy/docker-compose-dev.yml up --build

down:
	docker-compose -p vacancy -f deploy/docker-compose-dev.yml down

logs:
	docker-compose -p vacancy -f deploy/docker-compose-dev.yml logs -f --tail 30