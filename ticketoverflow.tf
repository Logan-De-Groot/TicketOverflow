resource "aws_ecs_cluster" "ticketoverflow" {
  name = "ticketoverflow"
}

resource "aws_ecs_task_definition" "ticketoverflow" {
  family                   = "ticketoverflow"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 4096
  memory                   = 8192
  execution_role_arn       = data.aws_iam_role.lab.arn

  container_definitions = <<DEFINITION
[
  {
    "image": "${aws_ecr_repository.ticketoverflow.repository_url}",
    "cpu": 4096,
    "memory": 8192,
    "name": "ticketoverflow",
    "networkMode": "awsvpc",
    "portMappings": [
      {
        "containerPort": 6400,
        "hostPort": 6400,
        "protocol": "tcp"
      }
    ],
    "environment": [
      {
        "name": "REDIS_URL",
        "value": "${aws_elasticache_cluster.redis.cache_nodes[0].address}"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.ticketoverflow.name}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }
]
DEFINITION
}



resource "aws_ecs_task_definition" "ticketoverflow_routines" {
  family                   = "ticketoverflow"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = data.aws_iam_role.lab.arn
  depends_on = [aws_ecs_task_definition.ticketoverflow ]
  container_definitions = <<DEFINITION
[
  {
    "image": "${aws_ecr_repository.ticketoverflow_routines.repository_url}",
    "cpu": 1024,
    "memory": 2048,
    "name": "ticketoverflow_routines",
    "networkMode": "awsvpc",
    "environment": [
      {
        "name": "REDIS_URL",
        "value": "${aws_elasticache_cluster.redis.cache_nodes[0].address}"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.ticketoverflow_routines.name}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }
]
DEFINITION
}

resource "aws_ecs_service" "ticketoverflow_routines" {
  name            = "ticketoverflow_routines"
  cluster         = aws_ecs_cluster.ticketoverflow.id
  task_definition = aws_ecs_task_definition.ticketoverflow_routines.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.ticketoverflow_target.id]
    assign_public_ip    = true
  }

  depends_on = [aws_security_group.ticketoverflow_routines]
}

resource "aws_ecs_service" "ticketoverflow" {
    name            = "ticketoverflow_ecs_service"
    cluster         = aws_ecs_cluster.ticketoverflow.id
    task_definition = aws_ecs_task_definition.ticketoverflow.arn
    desired_count   = 1
    launch_type     = "FARGATE"
    force_new_deployment = true

    network_configuration {
        subnets             = data.aws_subnets.private.ids
        security_groups     = [aws_security_group.ticketoverflow_target.id]
        assign_public_ip    = true
    }

    load_balancer {
        target_group_arn = aws_lb_target_group.ticketoverflow.arn
        container_name = "ticketoverflow"
        container_port = 6400
    }

    depends_on = [aws_lb_target_group.ticketoverflow]
}

resource "aws_cloudwatch_log_group" "ticketoverflow" {
  name = "/ticketoverflow"
}

resource "aws_cloudwatch_log_group" "ticketoverflow_routines" {
  name = "/ticketoverflow_routines"
}


resource "aws_security_group" "ticketoverflow_routines" {
  name        = "ticketoverflow_routines"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

    ingress {
      from_port = 6379
      to_port = 6379
      protocol = "tcp"
    }

    egress {
      from_port = 6379
      to_port = 6379
      protocol = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
}

