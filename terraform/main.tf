resource "aws_db_instance" "finace_instance" {
    identifier = "finace-data"
    allocated_storage = 20
    engine = "mysql"
    engine_version = "8.0"
    db_name = var.db_name
    instance_class = var.instance_class
    username = var.db_username
    password = var.db_password
}