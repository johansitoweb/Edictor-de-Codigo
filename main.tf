terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "app_image" {
  name         = "edictor-codigo:latest"
  build {
    context    = "."
    dockerfile = "Dockerfile"
  }
}

resource "docker_container" "app_container" {
  name  = "edictor-codigo"
  image = docker_image.app_image.name
  ports {
    internal = 8080
    external = 8080
  }
} 