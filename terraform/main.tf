data "aws_security_group" "rds" {
  id = "sg-043d834b3428841d2"
}
resource "aws_db_instance" "finance_instance" {
  identifier          = "finance-data"
  allocated_storage   = 20
  engine              = "mysql"
  engine_version      = "8.0"
  db_name             = var.db_name
  instance_class      = var.instance_class
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true
  publicly_accessible    = true
  vpc_security_group_ids = [data.aws_security_group.rds.id]
}
resource "aws_vpc_security_group_ingress_rule" "mysql_from_my_ip" {
  security_group_id = data.aws_security_group.rds.id
  cidr_ipv4         = var.my_ip_cidr
  from_port         = 3306
  to_port           = 3306
  ip_protocol       = "tcp"
  description       = "MySQL access from my IP"
}