resource "aws_ecs_cluster" "hamilton" {
  name = "hamilton"
}

resource "aws_ecs_task_definition" "hamilton_concerts" {
  family                   = "hamilton"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 4096
  memory                   = 8192
  execution_role_arn       = data.aws_iam_role.lab.arn
  depends_on = [aws_ecs_task_definition.hamilton_concerts]
  container_definitions = <<DEFINITION
[
  {
    "image": "${aws_ecr_repository.hamilton.repository_url}",
    "cpu": 4096,
    "memory": 8192,
    "name": "hamilton_concerts",
    "networkMode": "awsvpc",
    "environment": [
      {
        "name": "REDIS_URL",
        "value": "${aws_elasticache_cluster.redis.cache_nodes[0].address}"
      },
      {
        "name": "TICKETOVERFLOW_TYPE",
        "value": "concerts"
      },
      {
        "name": "MAX_NUMBER_ITEMS",
        "value": "5"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.hamilton_concerts.name}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }
]
DEFINITION
}


resource "aws_ecs_task_definition" "hamilton_tickets" {
  family                   = "hamilton"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 4096
  memory                   = 8192
  execution_role_arn       = data.aws_iam_role.lab.arn
  depends_on = [aws_ecs_task_definition.hamilton_concerts]
  container_definitions = <<DEFINITION
[
  {
    "image": "${aws_ecr_repository.hamilton.repository_url}",
    "cpu": 4096,
    "memory": 8192,
    "name": "hamilton_tickets",
    "networkMode": "awsvpc",
    "environment": [
      {
        "name": "REDIS_URL",
        "value": "${aws_elasticache_cluster.redis.cache_nodes[0].address}"
      },
      {
        "name": "TICKETOVERFLOW_TYPE",
        "value": "tickets"
      },
      {
        "name": "MAX_NUMBER_ITEMS",
        "value": "10"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${aws_cloudwatch_log_group.hamilton_tickets.name}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }
]
DEFINITION
}

resource "aws_security_group" "hamilton" {
  name        = "hamilton"

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

resource "aws_ecs_service" "hamilton_concerts" {
  name            = "hamilton_concerts"
  cluster         = aws_ecs_cluster.hamilton.id
  task_definition = aws_ecs_task_definition.hamilton_concerts.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.hamilton.id]
    assign_public_ip    = true
  }

}

resource "aws_ecs_service" "hamilton_tickets" {
  name            = "hamilton_tickets"
  cluster         = aws_ecs_cluster.hamilton.id
  task_definition = aws_ecs_task_definition.hamilton_tickets.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.hamilton.id]
    assign_public_ip    = true
  }

}


resource "aws_cloudwatch_log_group" "hamilton_concerts" {
  name = "/hamilton_concerts"
}


resource "aws_cloudwatch_log_group" "hamilton_tickets" {
  name = "/hamilton_tickets"
}


resource "aws_appautoscaling_target" "hamilton_concerts" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.hamilton.name}/${aws_ecs_service.hamilton_concerts.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}


resource "aws_appautoscaling_target" "hamilton_tickets" {
  max_capacity       = 6
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.hamilton.name}/${aws_ecs_service.hamilton_tickets.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}


resource "aws_cloudwatch_metric_alarm" "concerts_queue_length_scale_down_20" {
  alarm_name          = "concerts_queue_length_scale_down_20"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "120"
  statistic           = "Sum"
  threshold           = "20"
  alarm_description   = "Concerts Queue Length Scale Down"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_concerts_down.arn]
  dimensions = {
    QueueName = aws_sqs_queue.concert_queue.name
  }
}



resource "aws_appautoscaling_policy" "hamilton_concerts_down" {
  name               = "hamilton_concerts_down"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.hamilton_concerts.resource_id
  scalable_dimension = aws_appautoscaling_target.hamilton_concerts.scalable_dimension
  service_namespace  = aws_appautoscaling_target.hamilton_concerts.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Maximum"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "concerts_queue_length_scale_up" {
  alarm_name          = "concerts_queue_length_scale_up"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "30"
  statistic           = "Average"
  threshold           = "20"
  alarm_description   = "Concerts Queue Length Scale Up"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_concerts.arn]
  dimensions = {
    QueueName = aws_sqs_queue.concert_queue.name
  }
}


resource "aws_cloudwatch_metric_alarm" "concerts_queue_length_scale_up_40" {
  alarm_name          = "concerts_queue_length_scale_up_40"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "30"
  statistic           = "Average"
  threshold           = "40"
  alarm_description   = "Concerts Queue Length Scale Up"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_concerts.arn]
  dimensions = {
    QueueName = aws_sqs_queue.concert_queue.name
  }
}

resource "aws_appautoscaling_policy" "hamilton_concerts" {
  name               = "hamilton_concerts"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.hamilton_concerts.resource_id
  scalable_dimension = aws_appautoscaling_target.hamilton_concerts.scalable_dimension
  service_namespace  = aws_appautoscaling_target.hamilton_concerts.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = 1
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "tickets_queue_length" {
  alarm_name          = "tickets_queue_length"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "Tickets Queue Length"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_tickets.arn]
  dimensions = {
    QueueName = aws_sqs_queue.ticket_queue.name
  }
}

resource "aws_cloudwatch_metric_alarm" "tickets_queue_length_200" {
  alarm_name          = "tickets_queue_length_250"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "250"
  alarm_description   = "Tickets Queue Length"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_tickets.arn]
  dimensions = {
    QueueName = aws_sqs_queue.ticket_queue.name
  }
}

resource "aws_cloudwatch_metric_alarm" "tickets_queue_length_300" {
  alarm_name          = "tickets_queue_length_400"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "400"
  alarm_description   = "Tickets Queue Length"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_tickets.arn]
  dimensions = {
    QueueName = aws_sqs_queue.ticket_queue.name
  }
}

resource "aws_cloudwatch_metric_alarm" "tickets_queue_length_400" {
  alarm_name          = "tickets_queue_length_600"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "600"
  alarm_description   = "Tickets Queue Length"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_tickets.arn]
  dimensions = {
    QueueName = aws_sqs_queue.ticket_queue.name
  }
}

resource "aws_cloudwatch_metric_alarm" "tickets_queue_length_down" {
  alarm_name          = "tickets_queue_length_down"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Tickets Queue Length"
  alarm_actions       = [aws_appautoscaling_policy.hamilton_tickets_down.arn]
  dimensions = {
    QueueName = aws_sqs_queue.ticket_queue.name
  }
}


resource "aws_appautoscaling_policy" "hamilton_tickets" {
  name               = "hamilton_tickets"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.hamilton_tickets.id
  scalable_dimension = aws_appautoscaling_target.hamilton_tickets.scalable_dimension
  service_namespace  = aws_appautoscaling_target.hamilton_tickets.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = 1
    }
  }
}

resource "aws_appautoscaling_policy" "hamilton_tickets_down" {
  name               = "hamilton_tickets_down"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.hamilton_tickets.resource_id
  scalable_dimension = aws_appautoscaling_target.hamilton_tickets.scalable_dimension
  service_namespace  = aws_appautoscaling_target.hamilton_tickets.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Maximum"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}
