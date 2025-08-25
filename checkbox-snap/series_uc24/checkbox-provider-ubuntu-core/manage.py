#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# All rights reserved.

"""Management script for the ubuntu-core provider."""

from plainbox.provider_manager import setup
from plainbox.provider_manager import N_

setup(
    name='checkbox-provider-ubuntu-core',
    namespace='com.canonical.certification',
    version="0.1",
    description=N_("Checkbox Provider for ubuntu-core devices"),
    gettext_domain='checkbox-provider-ubuntu-core',
)
