
BUILD_DIR:=build

MODULES=gnupg bootstrap nailgun test os os/centos os/ubuntu iso cooks packages/rpm

.PHONY: all clean test test-unit help FORCE

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build nailgun bootstrap'
	@echo '  iso  - build nailgun iso'
	@echo '  test - run all tests'
	@echo '  test-unit - run unit tests'
	@echo '  test-integration - run integration tests'
	@echo '  test-cookbooks - run cookbooks tests'
	@echo '  clean-integration-test - clean integration test environment'
	@echo '  clean-cookbooks-test - clean cookbooks test environment'

all:

test: test-unit

test-unit:

# target to force rebuild of other targets
FORCE:

clean:
	rm -rf $(BUILD_DIR)

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))
find-files=$(shell test -d $1 && cd $1 && find * -type f 2> /dev/null)

include config.mk

define include-module-template
MODULE_SOURCE_DIR:=$1
MODULE_BUILD_DIR:=$(BUILD_DIR)/$1
.:=$$(MODULE_SOURCE_DIR)
/:=$$(MODULE_BUILD_DIR)/
$$/%: .:=$$.
$$/%: /:=$$/
include $1/module.mk
endef

include-module=$(eval $(call include-module-template,$1))

$(foreach module,$(MODULES),$(call include-module,$(module)))

include rules.mk

