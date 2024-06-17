#!/bin/bash

# Function to determine the Linux distribution
get_distro() {
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        echo "$ID $VERSION_ID"
    else
        echo "Unknown"
    fi
}

# Get the distribution
distro=$(get_distro)

# Check for CentOS 9 Stream
if [[ "$distro" == "centos 9" ]]; then
    echo "Detected CentOS 9 Stream. Running command for CentOS..."
    # Replace the following command with your desired action for CentOS
    dnf install --nogpgcheck https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm -E %rhel).noarch.rpm -y
    dnf install --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-$(rpm -E %rhel).noarch.rpm -y
    dnf install ffmpeg -y
elif [[ "$distro" == "debian 12" ]]; then
    echo "Detected Debian 12. Running command for Debian..."
    # Replace the following command with your desired action for Debian
    apt-get update && apt-get -y install ffmpeg
else
    echo "Unsupported or unknown distribution."
fi