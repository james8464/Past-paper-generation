APP_NAME := PaperCreator
APP_PROJECT := PaperCreator.xcodeproj
APP_WORKSPACE := PaperCreator.xcworkspace
APP_SCHEME ?= PaperCreator
APP_GENERATOR := xcodegen
CONFIGURATION ?= Debug
DISTRIBUTION_MODE ?= direct
APP_SANDBOX_ENABLED ?= NO
CODE_SIGN_ENTITLEMENTS_FILE ?= PaperCreator/PaperCreatorDirect.entitlements
CODE_SIGN_INJECT_BASE_ENTITLEMENTS ?= YES
TARGET_PREFIX :=
SCRIPTS_DIR := ./scripts

WORKSPACE ?= $(firstword $(wildcard *.xcworkspace))
PROJECT ?= $(firstword $(wildcard *.xcodeproj))
ifeq ($(strip $(PROJECT)),)
PROJECT := $(APP_PROJECT)
endif

ifeq ($(strip $(WORKSPACE)),)
BUILD_FILE_FLAG := -project $(PROJECT)
else
BUILD_FILE_FLAG := -workspace $(WORKSPACE)
endif

ifeq ($(TARGET_PREFIX),)
.DEFAULT_GOAL := build-and-run
endif

XCBUILD := $(SCRIPTS_DIR)/xcbuild.sh

ifeq ($(origin AGENT_NAME), undefined)
AGENT_NAME := $(shell $(SCRIPTS_DIR)/resolve_agent_name.sh)
endif

DERIVED_BASE := build/DerivedData
DERIVED := $(DERIVED_BASE)/$(AGENT_NAME)
LOG_DIR := build/logs/$(AGENT_NAME)
CACHE_ROOT := /tmp/papercreator-build/$(AGENT_NAME)/cache
TMPDIR_PATH := /tmp/papercreator-build/$(AGENT_NAME)/tmp

DESTINATION := platform=macOS,arch=arm64

BUILD_PRODUCTS := $(DERIVED)/Build/Products/$(CONFIGURATION)
APP_PATH := $(BUILD_PRODUCTS)/$(APP_SCHEME).app
APP_STORE_APP_PATH := $(DERIVED)/Build/Products/Release/$(APP_SCHEME).app
APP_STORE_HELPER_PATH := $(APP_STORE_APP_PATH)/Contents/Resources/PaperCreatorBackend/PaperCreatorBackend

PHONY_TARGETS := $(TARGET_PREFIX)help $(TARGET_PREFIX)diagnose $(TARGET_PREFIX)build \
	$(TARGET_PREFIX)test $(TARGET_PREFIX)run $(TARGET_PREFIX)build-and-run \
	$(TARGET_PREFIX)build-and-run-background $(TARGET_PREFIX)build-app-store \
	$(TARGET_PREFIX)preflight-app-store \
	$(TARGET_PREFIX)backend-env \
	$(TARGET_PREFIX)clean $(TARGET_PREFIX)agent-verify
.PHONY: $(PHONY_TARGETS)

$(TARGET_PREFIX)help:
	@printf "%s\n" \
		"Targets:" \
		"  make $(TARGET_PREFIX)build                    Build with strict flags + logs" \
		"  make $(TARGET_PREFIX)diagnose                 Print toolchain + config info" \
		"  make $(TARGET_PREFIX)test                     Run unit tests" \
		"  make $(TARGET_PREFIX)run                      Run app (assumes prior build)" \
		"  make $(TARGET_PREFIX)build-and-run            Build then run" \
		"  make $(TARGET_PREFIX)build-and-run-background Build then run in background" \
		"  make $(TARGET_PREFIX)build-app-store          Release build with App Store restrictions enabled" \
		"  make $(TARGET_PREFIX)preflight-app-store      Lint plist files and build App Store mode" \
		"  make $(TARGET_PREFIX)backend-env              Create the standalone-backend build environment" \
		"  make $(TARGET_PREFIX)clean                    Clean derived data + logs" \
		"  make $(TARGET_PREFIX)agent-verify             Build and test"

$(TARGET_PREFIX)diagnose:
	@APP_PROJECT="$(PROJECT)" \
		APP_WORKSPACE="$(WORKSPACE)" \
		APP_BUILD_FILE="$$( [ -n "$(WORKSPACE)" ] && printf "%s" "$(WORKSPACE)" || printf "%s" "$(PROJECT)" )" \
		APP_SCHEME="$(APP_SCHEME)" \
		APP_PLATFORM="macos" \
		APP_GENERATOR="$(APP_GENERATOR)" \
		APP_DESTINATION="$(DESTINATION)" \
		AGENT_NAME="$(AGENT_NAME)" \
		CACHE_ROOT="$(CACHE_ROOT)" \
		TMPDIR="$(TMPDIR_PATH)" \
		$(SCRIPTS_DIR)/diagnose.sh

$(TARGET_PREFIX)build:
	@LOG_DIR="$(LOG_DIR)" CACHE_ROOT="$(CACHE_ROOT)" TMPDIR="$(TMPDIR_PATH)" $(XCBUILD) --label "$(AGENT_NAME)" --action build -- \
		$(BUILD_FILE_FLAG) \
		-scheme $(APP_SCHEME) \
		-configuration $(CONFIGURATION) \
		-destination '$(DESTINATION)' \
		-derivedDataPath $(DERIVED) \
		GCC_TREAT_WARNINGS_AS_ERRORS=YES \
		SWIFT_TREAT_WARNINGS_AS_ERRORS=YES \
		SWIFT_STRICT_CONCURRENCY=complete \
		DISTRIBUTION_MODE=$(DISTRIBUTION_MODE) \
		APP_SANDBOX_ENABLED=$(APP_SANDBOX_ENABLED) \
		CODE_SIGN_ENTITLEMENTS_FILE=$(CODE_SIGN_ENTITLEMENTS_FILE) \
		CODE_SIGN_INJECT_BASE_ENTITLEMENTS=$(CODE_SIGN_INJECT_BASE_ENTITLEMENTS) \
		build

$(TARGET_PREFIX)test:
	@LOG_DIR="$(LOG_DIR)" CACHE_ROOT="$(CACHE_ROOT)" TMPDIR="$(TMPDIR_PATH)" $(XCBUILD) --label "$(AGENT_NAME)" --action test -- \
		$(BUILD_FILE_FLAG) \
		-scheme $(APP_SCHEME) \
		-configuration $(CONFIGURATION) \
		-destination '$(DESTINATION)' \
		-derivedDataPath $(DERIVED) \
		GCC_TREAT_WARNINGS_AS_ERRORS=YES \
		SWIFT_TREAT_WARNINGS_AS_ERRORS=YES \
		SWIFT_STRICT_CONCURRENCY=complete \
		DISTRIBUTION_MODE=$(DISTRIBUTION_MODE) \
		APP_SANDBOX_ENABLED=$(APP_SANDBOX_ENABLED) \
		CODE_SIGN_ENTITLEMENTS_FILE=$(CODE_SIGN_ENTITLEMENTS_FILE) \
		CODE_SIGN_INJECT_BASE_ENTITLEMENTS=$(CODE_SIGN_INJECT_BASE_ENTITLEMENTS) \
		test

$(TARGET_PREFIX)run:
	@$(SCRIPTS_DIR)/run_app_macos.sh --app-path "$(APP_PATH)"

$(TARGET_PREFIX)build-and-run: $(TARGET_PREFIX)build $(TARGET_PREFIX)run

$(TARGET_PREFIX)build-and-run-background: $(TARGET_PREFIX)build
	@$(SCRIPTS_DIR)/run_app_macos.sh --app-path "$(APP_PATH)" --background

$(TARGET_PREFIX)build-app-store:
	@$(MAKE) --no-print-directory $(TARGET_PREFIX)build CONFIGURATION=Release DISTRIBUTION_MODE=app-store APP_SANDBOX_ENABLED=YES CODE_SIGN_ENTITLEMENTS_FILE=PaperCreator/PaperCreator.entitlements CODE_SIGN_INJECT_BASE_ENTITLEMENTS=NO

$(TARGET_PREFIX)preflight-app-store:
	@plutil -lint PaperCreator/Info.plist PaperCreator/PrivacyInfo.xcprivacy PaperCreator/PaperCreator.entitlements PaperCreator/PaperCreatorBackend.entitlements
	@$(MAKE) --no-print-directory $(TARGET_PREFIX)build-app-store
	@codesign --verify --deep --strict --verbose=2 "$(APP_STORE_APP_PATH)"
	@codesign -d --entitlements :- "$(APP_STORE_APP_PATH)" 2>/dev/null | plutil -extract 'com\.apple\.security\.app-sandbox' raw -o - - | grep -qx true
	@codesign -d --entitlements :- "$(APP_STORE_HELPER_PATH)" 2>/dev/null | plutil -extract 'com\.apple\.security\.app-sandbox' raw -o - - | grep -qx true
	@codesign -d --entitlements :- "$(APP_STORE_HELPER_PATH)" 2>/dev/null | plutil -extract 'com\.apple\.security\.inherit' raw -o - - | grep -qx true
	@codesign -dvvv "$(APP_STORE_HELPER_PATH)" 2>&1 | grep -q 'runtime'
	@! find "$(APP_STORE_APP_PATH)" -iname '*Reference Corpus*' -print -quit | grep -q .

$(TARGET_PREFIX)backend-env:
	@$(SCRIPTS_DIR)/bootstrap_backend.sh

$(TARGET_PREFIX)clean:
	@$(SCRIPTS_DIR)/clean.sh

$(TARGET_PREFIX)agent-verify:
	@$(MAKE) --no-print-directory $(TARGET_PREFIX)build
	@$(MAKE) --no-print-directory $(TARGET_PREFIX)test
