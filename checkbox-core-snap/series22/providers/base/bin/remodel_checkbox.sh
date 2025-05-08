#!/bin/bash -e 

SOURCE_CHECKBOX_VERSION="$1"
TARGET_CHECKBOX_VERSION="$2"

# assumptions:
# checkbox$V must be in /root/checkbox$V.snap
# checkbox frontend must be in /root/checkbox.snap

# already happened?
if [ -e "/root/remodel_${TARGET_CHECKBOX_VERSION}.complete" ]; then
    exit 0
fi

# ensure remodel completed
if ! snap model | grep "ubuntu-core-${TARGET_CHECKBOX_VERSION}"; then
    exit 0
fi

# remove the old
snap remove checkbox
snap remove checkbox${SOURCE_CHECKBOX_VERSION}

# install the checkbox
snap install --dangerous "/root/checkbox${TARGET_CHECKBOX_VERSION}.snap"
snap install --dangerous --devmode /root/checkbox.snap

# do connections
snap connect checkbox:checkbox-runtime  checkbox${TARGET_CHECKBOX_VERSION}:checkbox-runtime
snap connect checkbox:provider-resource checkbox${TARGET_CHECKBOX_VERSION}:provider-resource
snap connect checkbox:provider-checkbox checkbox${TARGET_CHECKBOX_VERSION}:provider-checkbox
snap connect checkbox:provider-docker   checkbox${TARGET_CHECKBOX_VERSION}:provider-docker
snap connect checkbox:provider-tpm2     checkbox${TARGET_CHECKBOX_VERSION}:provider-tpm2
snap connect checkbox:provider-sru      checkbox${TARGET_CHECKBOX_VERSION}:provider-sru

# write marker
touch "/root/remodel_${TARGET_CHECKBOX_VERSION}.complete"
