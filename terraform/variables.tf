variable "db_name" {
  default = "mydb"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}
variable "instance_class" {
  default = "db.t3.micro"
}