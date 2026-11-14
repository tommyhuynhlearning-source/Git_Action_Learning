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
variable "my_ip_cidr" {
  type        = string
  description = "Your public IP in CIDR notation, for example 203.0.113.25/32"
}