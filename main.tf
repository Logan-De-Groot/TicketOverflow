terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 4.0"
        }
        docker = { 
            source = "kreuzwerker/docker" 
            version = "3.0.2" 
        } 
    }
}

provider "aws" {
    region = "us-east-1"
    shared_credentials_files = ["./credentials"]
    default_tags {
        tags = {
            Course       = "CSSE6400"
            Name         = "TicketOverflow"
            Automation   = "Terraform"
        }
    }

}



data "aws_ecr_authorization_token" "ecr_token" {

} 


data "aws_iam_role" "lab" {
name = "LabRole"
}


provider "docker" { 
 registry_auth { 
   address = data.aws_ecr_authorization_token.ecr_token.proxy_endpoint 
   username = data.aws_ecr_authorization_token.ecr_token.user_name 
   password = data.aws_ecr_authorization_token.ecr_token.password 
 } 
}


resource "aws_ecr_repository" "ticketoverflow" { 
 name = "ticketoverflow" 
}

resource "aws_ecr_repository" "ticketoverflow_routines" { 
 name = "ticketoverflow_routines" 
}

resource "docker_image" "ticketoverflow_routines" { 
 name = "${aws_ecr_repository.ticketoverflow_routines.repository_url}:latest" 
 build { 
   context = "ticketoverflow_routines" 
   dockerfile = "ticketoverflow_routines.dockerfile"
 } 
} 

resource "docker_image" "ticketoverflow" { 
 name = "${aws_ecr_repository.ticketoverflow.repository_url}:latest" 
 build { 
   context = "." 
   dockerfile = "Dockerfile"
 } 
} 

resource "aws_ecr_repository" "hamilton" { 
 name = "hamilton" 
}

resource "docker_image" "hamilton" { 
 name = "${aws_ecr_repository.hamilton.repository_url}:latest" 
 build { 
   context = "hamilton"
   dockerfile = "hamilton.dockerfile"
 } 
} 


 
resource "docker_registry_image" "ticketoverflow" { 
 name = docker_image.ticketoverflow.name 
}

resource "docker_registry_image" "hamilton" {
  name     = docker_image.hamilton.name
}


resource "docker_registry_image" "ticketoverflow_routines" {
  name     = docker_image.ticketoverflow_routines.name
}

data "aws_vpc" "default" {
    default = true
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

