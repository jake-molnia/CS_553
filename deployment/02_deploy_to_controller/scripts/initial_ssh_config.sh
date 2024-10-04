#!/bin/bash

# Function to handle errors
handle_error() {
  echo "Error: $1"
  exit 1
}

# Function to display usage information
usage() {
  echo "Usage: $0 -k <tailscale_auth_key>"
  echo "  -k    Tailscale authentication key"
  exit 1
}

# Parse command line arguments
while getopts "k:" opt; do
  case $opt in
  k) TAILSCALE_KEY="$OPTARG" ;;
  *) usage ;;
  esac
done

# Check if Tailscale key is provided
if [ -z "$TAILSCALE_KEY" ]; then
  usage
fi

# Function to test SSH connection
test_ssh_connection() {
  ssh -o BatchMode=yes -o ConnectTimeout=5 -J turing.wpi.edu app echo "SSH connection successful" >/dev/null 2>&1
}

# Backup the existing authorized_keys file
ssh -i /opt/CS_553/keys/student-admin-key -J turing.wpi.edu app <<EOF || handle_error "Failed to backup authorized_keys"
    cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak || handle_error "Failed to create backup of authorized_keys"
    echo "Backup of authorized_keys created"
EOF

# Update authorized_keys file with the new key while keeping existing keys
ssh -i /opt/CS_553/keys/student-admin-key -J turing.wpi.edu app <<EOF || handle_error "Failed to update authorized_keys"
    NEW_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIARTYgwoPW+VpBofWGYuHIldh18EUo42PHF/e08Dzcyp admin key CS553"
    if ! grep -q "\$NEW_KEY" ~/.ssh/authorized_keys; then
        echo "\$NEW_KEY" >> ~/.ssh/authorized_keys || handle_error "Failed to append new key to authorized_keys"
    fi
    chmod 600 ~/.ssh/authorized_keys || handle_error "Failed to set permissions on authorized_keys"
    echo "authorized_keys updated successfully"
EOF

# Test the SSH connection with the new key
if test_ssh_connection; then
  echo "SSH connection with new key successful"
else
  echo "SSH connection with new key failed. Restoring backup..."
  ssh -i /opt/CS_553/keys/student-admin-key -J turing.wpi.edu app <<EOF || handle_error "Failed to restore authorized_keys backup"
        cp ~/.ssh/authorized_keys.bak ~/.ssh/authorized_keys || handle_error "Failed to restore backup of authorized_keys"
        chmod 600 ~/.ssh/authorized_keys || handle_error "Failed to set permissions on restored authorized_keys"
        echo "Backup of authorized_keys restored"
EOF
  handle_error "SSH connection test failed. Original authorized_keys restored."
fi

# Install Tailscale and set up with provided key
ssh -J turing.wpi.edu app <<EOF || handle_error "Failed to set up Tailscale"
    # Install Tailscale
    curl -fsSL https://tailscale.com/install.sh | sh || handle_error "Failed to install Tailscale"

    # Run Tailscale with the provided auth key
    sudo tailscale up --authkey "$TAILSCALE_KEY" || handle_error "Failed to run Tailscale"

    echo "Tailscale setup completed successfully"
    exit
EOF

echo "Script completed successfully"
