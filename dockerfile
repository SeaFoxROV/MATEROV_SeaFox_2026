FROM osrf/ros:humble-desktop

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create non-root user + sudo
RUN groupadd --gid $USER_GID $USERNAME \
 && useradd -m -s /bin/bash --uid $USER_UID --gid $USER_GID $USERNAME \
 && apt-get update \
 && apt-get install -y sudo \
 && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME \
 && rm -rf /var/lib/apt/lists/*

# System dependencies
RUN apt-get update && apt-get install -y \
    nano \
    vim \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip3 install --no-cache-dir \
    opencv-python-headless \
    numpy==1.22

# Workspace
WORKDIR /home/ros/ros2_ws
COPY ros2_ws/src ./src

# Source ROS
RUN echo "source /opt/ros/humble/setup.bash" >> /home/ros/.bashrc

USER ros
CMD ["bash"]
