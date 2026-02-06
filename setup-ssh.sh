#!/bin/bash

# Define the SSH public key
PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDrlTS5/+T28q+/DN0RmH/XdC/f7m1fx8qz06AAkKO53GHKJj//d0hoPWYOpET1FVFDa4Gdo4u7Adn6xQLapwK/lXbJji//TWFSTvFuI4uOgmp2T740wAUoYM3oLB2s/At79L2MvKsODBm/DqilB1RrOQrZxPyGcCI/0XP37l+P+j+zNsOQ88m7jAxlfFM9L7uiqKV5c6INxxp/c1+dyDMOCevTHrhqISYIIrLU4UUC/AftggydDslGd8aSjMOK0U5DjFFWcBvJKRFjkxDNojoHdTe/Qtz3v846vdUmrYAx8HJE22+x/cEKTnrP7/ijzoXEDG33a7lkvgHYOSeUBuFVXxu5izuk5uo6dZCdRL2Ep/cRMJRdhGh9TL0hq1udN9R4imR++HizBWrmgw4uIvSigOAhcJpd5drSNkJZl8AjxC4EPlUwbSUAIXyU9233hVTr9GvHnBD0y3ptikgb37tzCCgid3ivUYxJ3CuWfhidLa7ZmeDSZ5pTvDWfjoxPAtUstPsT8EXcTdMXFrR6X3pA3nZz+/0NS1rZ6d7Q7f/aFFiYfPp0vyAdlufXA+aLFUUCjtLf1n9+G1RzcBnIuFbwLC0ZvWCN6IAZwiTu6lEAsRkoBzwZzilGV0BnIQdbCdOBFFlVQftlUqd+xN0M9hMG+SbaZg5NU+nuvuF3wflrnQ== vunts@stsbmt.com"

# Set the path to the root user's SSH directory and authorized_keys file
ROOT_SSH_DIR="/root/.ssh"
AUTHORIZED_KEYS="${ROOT_SSH_DIR}/authorized_keys"

# Create the .ssh directory if it doesn't exist
if [ ! -d "$ROOT_SSH_DIR" ]; then
  echo "Creating .ssh directory for root user..."
  mkdir -p "$ROOT_SSH_DIR"
  chmod 700 "$ROOT_SSH_DIR"
fi

# Create the authorized_keys file if it doesn't exist
if [ ! -f "$AUTHORIZED_KEYS" ]; then
  touch "$AUTHORIZED_KEYS"
  chmod 600 "$AUTHORIZED_KEYS"
fi

# Add the public key only if it's not already in the file
if ! grep -qF "$PUBLIC_KEY" "$AUTHORIZED_KEYS"; then
  echo "Adding public key to root's authorized_keys..."
  echo "$PUBLIC_KEY" >> "$AUTHORIZED_KEYS"
  echo "Public key added successfully."
else
  echo "Public key already exists in authorized_keys."
fi

# Set correct ownership and permissions again just in case
chown -R root:root "$ROOT_SSH_DIR"
chmod 700 "$ROOT_SSH_DIR"
chmod 600 "$AUTHORIZED_KEYS"

echo "Done."

# Optional: clear command history (only current session)
history -c
