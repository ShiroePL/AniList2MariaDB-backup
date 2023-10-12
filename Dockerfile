# Set the base image to Alpine Linux
FROM alpine:latest

# Update package list and install bash, ZeroTier, and Python
RUN apk update && \
    apk add --no-cache bash python3

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set the entrypoint to tail -f /dev/null to keep the container running
ENTRYPOINT ["tail", "-f", "/dev/null"]