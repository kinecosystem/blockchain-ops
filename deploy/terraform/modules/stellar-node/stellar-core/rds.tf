module "rds" {
  source = "terraform-aws-modules/rds/aws"

  identifier = "${var.name}"

  engine               = "postgres"
  engine_version       = "9.6.6"
  parameter_group_name = "default.postgres9.6"
  option_group_name    = "default:postgres-9-6"

  vpc_security_group_ids = ["${module.rds_security_group.this_security_group_id}"]

  subnet_ids             = ["${data.aws_subnet.default.id}"]
  availability_zone      = "${data.aws_subnet.default.availability_zone}"
  create_db_subnet_group = false                                          # use default

  instance_class    = "db.t2.medium"
  storage_type      = "standard"     # magnetic
  allocated_storage = 20

  name     = "core"
  username = "stellar"
  password = "${var.rds_password}"
  port     = "5432"

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_retention_period = 0
  backup_window           = "03:00-06:00"

  tags = {
    Type    = "stellar-core"
    network = "${var.stellar_network_name}"
  }
}

module "rds_security_group" {
  source = "terraform-aws-modules/security-group/aws"

  name                = "${var.name}-rds"
  description         = "RDS access for all instances in the VPC"
  vpc_id              = "${data.aws_vpc.default.id}"
  ingress_cidr_blocks = ["${data.aws_vpc.default.cidr_block}"]
  ingress_rules       = ["postgresql-tcp"]
}
