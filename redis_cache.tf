

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "redis"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  engine_version       = "6.x"
  security_group_ids   = [aws_security_group.redis_sg.id]
  
}


resource "aws_security_group" "redis_sg" {
  name = "redis-security-group"

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.ticketoverflow_target.id, aws_security_group.hamilton.id]
  }
}

resource "aws_elasticache_subnet_group" "subnet_group" {
  name       = "redis-subnet-group"
  subnet_ids = data.aws_subnets.private.ids
}