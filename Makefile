# Image URL to use all building/pushing image targets
# IMG ?= europe-west4-docker.pkg.dev/aidence-management/aidence-docker/postgres-database-operator:latest
IMG ?= solidnerd/postgres-database-operator:latest

SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec

help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: build

all: build

build: docker-build

docker-build: ## Build docker image with the manager.
	docker build -t ${IMG} .

docker-push: ## Push docker image with the manager.
	docker push ${IMG}

