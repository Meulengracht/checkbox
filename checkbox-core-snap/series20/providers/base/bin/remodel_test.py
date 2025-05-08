#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# All rights reserved.
#
# Written by:
#    Authors: Philip Meulengracht <philip.meulengracht@canonical.com>

import argparse
import os
import platform
import subprocess
from urllib.request import urlretrieve


# the remodel script for checkbox
remodel_checkbox_script = """#!/bin/bash -e

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
"""  # noqa: E501


def previous_uc_ver(uc_ver):
    uci = int(uc_ver)
    return str(uci - 2)


def write_remodel_script():
    with open("/root/remodel-checkbox.sh", "w") as f:
        f.write(remodel_checkbox_script)
    os.chmod("/root/remodel-checkbox.sh", 0o700)


def write_systemd_service(uc_ver):
    prev_ver = previous_uc_ver(uc_ver)
    with open("/etc/systemd/system/remodel-checkbox.service", "w") as f:
        f.write("[Unit]\n")
        f.write("Description=Remodel checkbox service\n")
        f.write("After=snapd.service\n")
        f.write("Requires=snapd.service\n\n")
        f.write("[Service]\n")
        f.write("Type=simple\n")
        f.write(f"ExecStart=/root/remodel-checkbox.sh {prev_ver} {uc_ver}\n\n")
        f.write("[Install]\n")
        f.write("WantedBy=multi-user.target\n")


def enable_systemd_service():
    subprocess.run(
        [
            "systemctl",
            "daemon-reload",
        ]
    )
    subprocess.run(
        [
            "systemctl",
            "enable",
            "remodel-checkbox.service",
        ]
    )


def get_platform():
    plt = platform.platform()
    if "raspi-aarch64" in plt:
        return "pi-arm64"
    elif "raspi" in plt:
        return "pi-armhf"
    elif "x86_64" in plt:
        return "amd64"
    raise SystemExit(f"platform not supported for remodeling test: {plt}")


# Currently images used in certifications are sourced from cdimage,
# those images builds using the models supplied in canonical/models.
# Make sure we use the same models that come from the same authority,
# otherwise remodeling will fail.
def download_model(uc_ver):
    base_uri = "https://raw.githubusercontent.com/canonical/models/"
    branch = "refs/heads/master/"
    model = f"ubuntu-core-{uc_ver}-{get_platform()}-dangerous.model"
    print(f"downloading model for remodeling: {base_uri + branch + model}")
    path, _ = urlretrieve(base_uri + branch + model)
    return path


# downloads a snap to the tmp folder
def download_snap(name, out, channel):
    dir = os.getcwd()
    os.chdir("/tmp")
    subprocess.run(
        [
            "snap",
            "download",
            name,
            f"--channel=latest/{channel}",
            f"--basename={out}",
        ]
    )
    os.chdir(dir)


def download_snaps(uc_ver):
    # use stable for remodel, we are not testing the snaps we are
    # remodeling to, but rather the process works.
    channel = "stable"
    download_snap(f"core{uc_ver}", "base", channel)
    if "pi" in get_platform():
        download_snap("pi", "gadget", f"--channel={uc_ver}/{channel}")
        download_snap("pi-kernel", "kernel", f"--channel={uc_ver}/{channel}")
    else:
        download_snap("pc", "gadget", f"--channel={uc_ver}/{channel}")
        download_snap("pc-kernel", "kernel", f"--channel={uc_ver}/{channel}")


def main():
    """Run remodel of an Ubuntu Core host."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target",
        help="which verison of ubuntu-core that should be remodeled to",
        choices=["22", "24"],
    )

    # resolve the snaps for the remodel if offline has been requested
    # (currently offline was used for testing in certain scenarios during
    # test development) - for normal testing offline should not be needed
    parser.add_argument(
        "--offline",
        help="whether the remodel should be offline",
        action='store_true',
    )
    args = parser.parse_args()

    # resolve the model for the current platform
    model_path = download_model(args.target)

    # prepare checkbox remodel
    write_remodel_script()
    write_systemd_service(args.target)
    enable_systemd_service()

    if args.offline:
        download_snaps(args.target)

        # instantiate the offline remodel
        print("initiating offline device remodel")
        subprocess.run(
            [
                "sudo",
                "snap",
                "remodel",
                "--offline",
                "--snap",
                "/tmp/base.snap",
                "--assertion",
                "/tmp/base.assert",
                "--snap",
                "/tmp/gadget.snap",
                "--assertion",
                "/tmp/gadget.assert",
                "--snap",
                "/tmp/kernel.snap",
                "--assertion",
                "/tmp/kernel.assert",
                model_path,
            ]
        )
    else:
        # instantiate the remodel
        print("initiating device remodel")
        #subprocess.run(["sudo", "snap", "remodel", model_path])


if __name__ == "__main__":
    exit(main())
