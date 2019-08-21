__PHONY__: build build-testing

CORE_VERSION := kinecosystem-v2.1.0-stellar-v9.2.0
HORIZON_VERSION := v2.1.0

core-binary:
	docker pull kinecosystem/stellar-core:${CORE_VERSION}
	docker run -d --name stellar-core-binary --rm --entrypoint sleep kinecosystem/stellar-core:${CORE_VERSION} 5
	docker cp $$(docker inspect --format="{{.Id}}" stellar-core-binary):/usr/local/bin/stellar-core ./

horizon-binary:
	docker pull kinecosystem/horizon:${HORIZON_VERSION}
	docker run -d --name horizon-binary --rm --entrypoint sleep kinecosystem/horizon:${HORIZON_VERSION} 5
	docker cp $$(docker inspect --format="{{.Id}}" horizon-binary):/usr/local/bin/horizon ./

build: core-binary horizon-binary
	docker build -t kinecosystem/blockchain-quickstart -f Dockerfile .

build-testing: core-binary horizon-binary
	docker build -t kinecosystem/blockchain-quickstart:testing -f Dockerfile.testing .
