# --- RDS Subnet Group ---

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = "production"
  }
}

# --- RDS Security Group ---

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Allow inbound PostgreSQL traffic from EC2"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL from EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Environment = "production"
  }
}

# --- RDS DB Instance (PostgreSQL) ---

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  db_name                = "cloudwise"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t4g.micro"
  username               = "cloudwise_admin"
  password               = "CloudWisePassProd123!"
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true

  tags = {
    Name        = "${var.project_name}-db-instance"
    Environment = "production"
  }
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}
